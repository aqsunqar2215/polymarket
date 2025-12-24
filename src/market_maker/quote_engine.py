from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import structlog

from src.config import Settings
from src.inventory.inventory_manager import InventoryManager

logger = structlog.get_logger(__name__)


@dataclass
class Quote:
    side: str
    price: float
    size: float
    market: str
    token_id: str


class QuoteEngine:
    def __init__(self, settings: Settings, inventory_manager: InventoryManager):
        self.settings = settings
        self.inventory_manager = inventory_manager

    def calculate_bid_price(self, mid_price: float, spread_bps: int) -> float:
        return mid_price * (1 - spread_bps / 10000)

    def calculate_ask_price(self, mid_price: float, spread_bps: int) -> float:
        return mid_price * (1 + spread_bps / 10000)

    def calculate_mid_price(self, best_bid: float, best_ask: float) -> float:
        if best_bid <= 0 or best_ask <= 0:
            return 0.0
        return (best_bid + best_ask) / 2.0

    def generate_quotes(
        self, market_id: str, best_bid: float, best_ask: float, yes_token_id: str, no_token_id: str
    ) -> tuple[Quote | None, Quote | None]:
        mid_price = self.calculate_mid_price(best_bid, best_ask)
        
        if mid_price == 0:
            return (None, None)

        spread_bps = self.settings.min_spread_bps
        
        bid_price = self.calculate_bid_price(mid_price, spread_bps)
        ask_price = self.calculate_ask_price(mid_price, spread_bps)
        
        base_size = self.settings.default_size
        
        yes_size = self.inventory_manager.get_quote_size_yes(base_size, mid_price)
        no_size = self.inventory_manager.get_quote_size_no(base_size, mid_price)
        
        yes_quote = None
        no_quote = None
        
        if self.inventory_manager.can_quote_yes(yes_size):
            yes_quote = Quote(
                side="BUY",
                price=bid_price,
                size=yes_size,
                market=market_id,
                token_id=yes_token_id,
            )
        
        if self.inventory_manager.can_quote_no(no_size):
            no_quote = Quote(
                side="BUY",
                price=1.0 - ask_price,
                size=no_size,
                market=market_id,
                token_id=no_token_id,
            )
        
        return (yes_quote, no_quote)

    def adjust_for_inventory_skew(self, base_size: float, price: float, side: str) -> float:
        skew = self.inventory_manager.inventory.get_skew()
        
        if skew > 0.2:
            if side == "BUY" and self.inventory_manager.inventory.net_exposure_usd > 0:
                return base_size * 0.5
            elif side == "SELL" and self.inventory_manager.inventory.net_exposure_usd < 0:
                return base_size * 0.5
        
        return base_size

    def should_trim_quotes(self, time_to_close_hours: float) -> bool:
        if time_to_close_hours < 1.0:
            return True
        return False

