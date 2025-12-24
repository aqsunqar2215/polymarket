from __future__ import annotations

from typing import Any

import httpx
import structlog

from src.config import Settings

logger = structlog.get_logger(__name__)


class AutoRedeem:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = httpx.AsyncClient(timeout=30.0)

    async def check_redeemable_positions(self, address: str) -> list[dict[str, Any]]:
        try:
            # Try CLOB API for positions
            response = await self.client.get(
                f"{self.settings.polymarket_clob_url}/user/{address}/positions",
            )
            
            if response.status_code == 404:
                logger.debug("positions_endpoint_not_available", address=address)
                return []
            
            response.raise_for_status()
            data = response.json()
            
            # Filter for redeemable positions
            if isinstance(data, list):
                return [p for p in data if isinstance(p, dict) and p.get("redeemable", False)]
            elif isinstance(data, dict) and "positions" in data:
                positions = data["positions"]
                return [p for p in positions if isinstance(p, dict) and p.get("redeemable", False)]
            
            return []
        except Exception as e:
            logger.debug("redeemable_positions_check_failed", error=str(e), address=address)
            return []

    async def redeem_position(self, position_id: str) -> bool:
        try:
            response = await self.client.post(
                f"{self.settings.polymarket_clob_url}/positions/{position_id}/redeem",
            )
            response.raise_for_status()
            logger.info("position_redeemed", position_id=position_id)
            return True
        except Exception as e:
            logger.debug("position_redeem_failed", position_id=position_id, error=str(e))
            return False

    async def auto_redeem_all(self, address: str) -> int:
        if not self.settings.auto_redeem_enabled:
            return 0
        
        redeemable = await self.check_redeemable_positions(address)
        redeemed = 0
        
        for position in redeemable:
            value_usd = float(position.get("value", 0))
            if value_usd >= self.settings.redeem_threshold_usd:
                if await self.redeem_position(position.get("id")):
                    redeemed += 1
        
        if redeemed > 0 or len(redeemable) > 0:
            logger.info("auto_redeem_completed", redeemed=redeemed, total=len(redeemable))
        
        return redeemed

    async def close(self):
        await self.client.aclose()