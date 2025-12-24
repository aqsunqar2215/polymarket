from __future__ import annotations

from typing import Any

import httpx
import structlog

from src.config import Settings

logger = structlog.get_logger(__name__)


class PolymarketRestClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = settings.polymarket_api_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def get_markets(self, active: bool = True, closed: bool = False) -> list[dict[str, Any]]:
        try:
            response = await self.client.get(f"{self.base_url}/markets")
            response.raise_for_status()
            
            data = response.json()
            logger.debug("markets_api_response", data_type=type(data), count=len(data) if isinstance(data, list) else "N/A")
            
            # Gamma API returns a list directly
            if isinstance(data, list):
                # If we have markets, use them (Gamma API doesn't support query params)
                # Just filter by active status
                if active:
                    filtered = [m for m in data if isinstance(m, dict) and m.get("active", False)]
                else:
                    filtered = data
                
                logger.info("markets_found", total=len(data), filtered=len(filtered))
                return filtered
            elif isinstance(data, dict):
                # Handle wrapped response
                if "data" in data and isinstance(data["data"], list):
                    return data["data"]
                return []
            else:
                logger.warning("unexpected_markets_response_type", response_type=type(data))
                return []
        except Exception as e:
            logger.error("markets_fetch_failed", error=str(e), exc_info=True)
            raise

    async def search_markets(self, query: str = "") -> list[dict[str, Any]]:
        """Search for markets by query string"""
        try:
            params = {}
            if query:
                params["query"] = query
            response = await self.client.get(f"{self.base_url}/search", params=params)
            response.raise_for_status()
            
            data = response.json()
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "markets" in data:
                return data["markets"]
            return []
        except Exception as e:
            logger.error("markets_search_failed", query=query, error=str(e))
            return []

    async def get_orderbook(self, market_id: str) -> dict[str, Any]:
        try:
            # Gamma API includes orderbook data in market info
            response = await self.client.get(f"{self.base_url}/markets/{market_id}")
            response.raise_for_status()
            
            data = response.json()
            
            # Extract orderbook data from market info
            orderbook = {
                "best_bid": float(data.get("bestBid", 0)),
                "best_ask": float(data.get("bestAsk", 1)),
                "market_id": market_id,
                "last_trade_price": float(data.get("lastTradePrice", 0.5)),
                "spread": data.get("spread", 0),
            }
            
            logger.debug("orderbook_fetched", market_id=market_id, best_bid=orderbook["best_bid"], best_ask=orderbook["best_ask"])
            return orderbook
        except Exception as e:
            logger.error("orderbook_fetch_failed", market_id=market_id, error=str(e))
            raise

    async def get_market_info(self, market_id: str) -> dict[str, Any]:
        try:
            # Try gamma API first (expects market_id as slug)
            response = await self.client.get(f"{self.base_url}/markets/{market_id}")
            response.raise_for_status()
            
            data = response.json()
            logger.debug("market_info_fetched", market_id=market_id, keys=list(data.keys()) if isinstance(data, dict) else "N/A")
            return data
        except Exception as e:
            logger.error("market_info_fetch_failed", market_id=market_id, error=str(e), exc_info=True)
            raise

    async def get_balances(self, address: str) -> dict[str, Any]:
        try:
            response = await self.client.get(f"{self.base_url}/balances", params={"user": address})
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("balances_fetch_failed", address=address, error=str(e))
            raise

    async def get_open_orders(self, address: str, market_id: str | None = None) -> list[dict[str, Any]]:
        try:
            params = {"user": address}
            if market_id:
                params["market"] = market_id
            response = await self.client.get(f"{self.base_url}/open-orders", params=params)
            response.raise_for_status()
            
            data = response.json()
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "orders" in data:
                return data["orders"]
            return []
        except Exception as e:
            logger.error("open_orders_fetch_failed", address=address, error=str(e))
            raise

    async def close(self):
        await self.client.aclose()