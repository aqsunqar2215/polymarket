from __future__ import annotations

from typing import Any

import structlog

from src.config import Settings
from src.inventory.inventory_manager import InventoryManager

logger = structlog.get_logger(__name__)


class RiskManager:
    def __init__(self, settings: Settings, inventory_manager: InventoryManager):
        self.settings = settings
        self.inventory_manager = inventory_manager

    def check_exposure_limits(self, proposed_size_usd: float, side: str) -> bool:
        current_exposure = self.inventory_manager.inventory.net_exposure_usd
        
        if side == "BUY":
            new_exposure = current_exposure + proposed_size_usd
            if new_exposure > self.settings.max_exposure_usd:
                logger.warning(
                    "exposure_limit_exceeded",
                    current=current_exposure,
                    proposed=new_exposure,
                    limit=self.settings.max_exposure_usd,
                )
                return False
        
        elif side == "SELL":
            new_exposure = current_exposure - proposed_size_usd
            if new_exposure < self.settings.min_exposure_usd:
                logger.warning(
                    "exposure_limit_exceeded",
                    current=current_exposure,
                    proposed=new_exposure,
                    limit=self.settings.min_exposure_usd,
                )
                return False
        
        return True

    def check_position_size(self, size_usd: float) -> bool:
        if size_usd > self.settings.max_position_size_usd:
            logger.warning(
                "position_size_exceeded",
                size=size_usd,
                max=self.settings.max_position_size_usd,
            )
            return False
        return True

    def check_inventory_skew(self) -> bool:
        skew = self.inventory_manager.inventory.get_skew()
        if skew > self.settings.inventory_skew_limit:
            logger.warning("inventory_skew_exceeded", skew=skew, limit=self.settings.inventory_skew_limit)
            return False
        return True

    def validate_order(self, side: str, size_usd: float) -> tuple[bool, str]:
        if not self.check_position_size(size_usd):
            return (False, "Position size exceeds limit")
        
        if not self.check_exposure_limits(size_usd, side):
            return (False, "Exposure limit exceeded")
        
        if not self.check_inventory_skew():
            return (False, "Inventory skew too high")
        
        return (True, "OK")

    def should_stop_trading(self) -> bool:
        exposure = abs(self.inventory_manager.inventory.net_exposure_usd)
        max_exposure = abs(self.settings.max_exposure_usd)
        
        if exposure > max_exposure * 0.9:
            logger.warning("near_exposure_limit", exposure=exposure, max=max_exposure)
            return True
        
        return False

