from __future__ import annotations

import asyncio
import signal
import time
from typing import Any

import structlog
from dotenv import load_dotenv

from src.config import Settings, get_settings
from src.execution.order_executor import OrderExecutor
from src.inventory.inventory_manager import InventoryManager
from src.logging_config import configure_logging
from src.market_maker.quote_engine import QuoteEngine
from src.polymarket.order_signer import OrderSigner
from src.polymarket.rest_client import PolymarketRestClient
from src.polymarket.websocket_client import PolymarketWebSocketClient
from src.risk.risk_manager import RiskManager
from src.services import AutoRedeem, start_metrics_server

logger = structlog.get_logger(__name__)


class MarketMakerBot:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.running = False
        self.rest_client = PolymarketRestClient(settings)
        self.ws_client = PolymarketWebSocketClient(settings)
        self.order_signer = OrderSigner(settings.private_key)
        self.order_executor = OrderExecutor(settings, self.order_signer)
        
        self.inventory_manager = InventoryManager(
            settings.max_exposure_usd,
            settings.min_exposure_usd,
            settings.target_inventory_balance,
        )
        self.risk_manager = RiskManager(settings, self.inventory_manager)
        self.quote_engine = QuoteEngine(settings, self.inventory_manager)
        
        self.auto_redeem = AutoRedeem(settings)
        
        self.current_orderbook: dict[str, Any] = {}
        self.open_orders: dict[str, dict[str, Any]] = {}
        self.last_quote_time = 0.0
        self.market_id: str | None = None

    async def discover_market(self) -> dict[str, Any] | None:
        # First, try to use provided market_id or extract from URL
        market_id = self.settings.get_market_id()
        
        if market_id:
            logger.info("using_provided_market_id", market_id=market_id)
            self.market_id = market_id
            try:
                market_info = await self.rest_client.get_market_info(market_id)
                logger.info("market_found", market_id=market_id, question=market_info.get("question"))
                return market_info
            except Exception as e:
                logger.error("failed_to_fetch_provided_market", market_id=market_id, error=str(e))
                return None
        
        # If no market_id provided and auto_discover enabled, find first active market
        if self.settings.auto_discover_markets:
            logger.info("auto_discovering_markets")
            try:
                markets = await self.rest_client.get_markets(active=True, closed=False)
                
                logger.debug("markets_response", count=len(markets) if isinstance(markets, list) else 0)
                
                if not markets or (isinstance(markets, list) and len(markets) == 0):
                    logger.error("no_active_open_markets_found")
                    return None
                
                if not isinstance(markets, list):
                    logger.error("unexpected_markets_format", response_type=type(markets))
                    return None
                
                # Get first market from filtered list
                first_market = markets[0]
                
                if isinstance(first_market, dict):
                    # Gamma API uses 'id' field
                    market_id = first_market.get("id")
                    if not market_id:
                        market_id = first_market.get("slug")
                else:
                    logger.error("unexpected_market_format", market_type=type(first_market))
                    return None
                
                if not market_id:
                    logger.error("could_not_extract_market_id")
                    return None
                
                self.market_id = market_id
                market_question = first_market.get("question", "")
                logger.info(
                    "auto_discovered_market",
                    market_id=market_id,
                    question=market_question[:100] if market_question else "",
                    active=first_market.get("active"),
                    closed=first_market.get("closed")
                )
                
                # Return the market data we already have
                return first_market
                    
            except Exception as e:
                logger.error("market_discovery_failed", error=str(e), exc_info=True)
                return None
        
        logger.error("no_market_configured_and_discovery_disabled")
        return None

    async def update_orderbook(self):
        if not self.market_id:
            logger.warning("cannot_update_orderbook_no_market_id")
            return
        
        try:
            orderbook = await self.rest_client.get_orderbook(self.market_id)
            self.current_orderbook = orderbook
            logger.debug("orderbook_updated", best_bid=orderbook.get("best_bid"), best_ask=orderbook.get("best_ask"))
        except Exception as e:
            logger.error("orderbook_update_failed", market_id=self.market_id, error=str(e))

    def _handle_orderbook_update(self, data: dict[str, Any]):
        if self.market_id and data.get("market") == self.market_id:
            self.current_orderbook = data.get("book", self.current_orderbook)

    async def refresh_quotes(self, market_info: dict[str, Any]):
        current_time = time.time() * 1000
        elapsed = current_time - self.last_quote_time
        
        if elapsed < self.settings.quote_refresh_rate_ms:
            return
        
        self.last_quote_time = current_time
        
        orderbook = self.current_orderbook
        if not orderbook:
            await self.update_orderbook()
            orderbook = self.current_orderbook
        
        best_bid = float(orderbook.get("best_bid", 0)) if orderbook else 0
        best_ask = float(orderbook.get("best_ask", 1)) if orderbook else 1
        
        # Skip invalid orderbooks
        if best_bid <= 0 or best_ask >= 1 or best_bid >= best_ask:
            logger.debug("skipping_invalid_orderbook", best_bid=round(best_bid, 6), best_ask=round(best_ask, 6))
            return
        
        yes_token_id = market_info.get("yes_token_id", "")
        no_token_id = market_info.get("no_token_id", "")
        
        if not self.market_id:
            logger.warning("cannot_generate_quotes_no_market_id")
            return
        
        yes_quote, no_quote = self.quote_engine.generate_quotes(
            self.market_id, best_bid, best_ask, yes_token_id, no_token_id
        )
        
        # Calculate spread in basis points
        spread_bps = int((best_ask - best_bid) / ((best_bid + best_ask) / 2) * 10000)
        mid_price = (best_bid + best_ask) / 2
        
        # Log market information
        logger.info(
    "market_quote_update",
    market_id=self.market_id,
    question=market_info.get("question", "")[:80],
    best_bid=round(best_bid, 6),
    best_ask=round(best_ask, 6),
    mid_price=round(mid_price, 6),
    spread_bps=spread_bps,
    volume_24h=round(float(market_info.get('volume24hr', 0) or 0), 2),
    liquidity=round(float(market_info.get('liquidity', 0) or 0), 2),
)
        
        if yes_quote:
            logger.info(
                "yes_quote",
                side=yes_quote.side,
                price=round(yes_quote.price, 6),
                size=round(yes_quote.size, 2),
                distance_from_bid_bps=int((yes_quote.price - best_bid) / best_bid * 10000) if best_bid > 0 else 0,
            )
        
        if no_quote:
            logger.info(
                "no_quote",
                side=no_quote.side,
                price=round(no_quote.price, 6),
                size=round(no_quote.size, 2),
                distance_from_ask_bps=int((best_ask - no_quote.price) / best_ask * 10000) if best_ask > 0 else 0,
            )

    async def run_cancel_replace_cycle(self, market_info: dict[str, Any]):
        while self.running:
            try:
                await self.refresh_quotes(market_info)
                await asyncio.sleep(self.settings.cancel_replace_interval_ms / 1000.0)
            except Exception as e:
                logger.error("cancel_replace_cycle_error", error=str(e))
                await asyncio.sleep(1)

    async def run_auto_redeem(self):
        while self.running:
            try:
                if self.settings.auto_redeem_enabled:
                    await self.auto_redeem.auto_redeem_all(self.order_signer.get_address())
                await asyncio.sleep(300)
            except Exception as e:
                logger.error("auto_redeem_error", error=str(e))
                await asyncio.sleep(60)

    async def run(self):
        self.running = True
        
        logger.info("market_maker_starting")
        
        market_info = await self.discover_market()
        if not market_info:
            logger.error("market_discovery_failed_cannot_start")
            return
        
        logger.info("market_maker_initialized", market_id=self.market_id)
        
        await self.update_orderbook()
        
        if self.settings.market_discovery_enabled:
            await self.ws_client.connect()
            await self.ws_client.subscribe_orderbook(self.market_id)
        
        tasks = [
            self.run_cancel_replace_cycle(market_info),
            self.run_auto_redeem(),
        ]
        
        if self.ws_client.running:
            tasks.append(self.ws_client.listen())
        
        try:
            await asyncio.gather(*tasks)
        finally:
            await self.cleanup()

    async def cleanup(self):
        self.running = False
        await self.rest_client.close()
        await self.ws_client.close()
        await self.order_executor.close()
        await self.auto_redeem.close()
        logger.info("market_maker_shutdown_complete")


async def bootstrap(settings: Settings):
    load_dotenv()
    configure_logging(settings.log_level)
    start_metrics_server(settings.metrics_host, settings.metrics_port)

    bot = MarketMakerBot(settings)

    loop = asyncio.get_event_loop()
    stop_event = asyncio.Event()

    def _handle_signal():
        logger.info("shutdown_signal_received")
        bot.running = False
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handle_signal)
        except NotImplementedError:
            pass

    try:
        await bot.run()
    finally:
        logger.info("bot_shutdown_complete")


def main():
    settings = get_settings()
    asyncio.run(bootstrap(settings))


if __name__ == "__main__":
    main()