from __future__ import annotations

from typing import Any

from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3
import structlog

logger = structlog.get_logger(__name__)


class OrderSigner:
    def __init__(self, private_key: str):
        self.account = Account.from_key(private_key)
        self.web3 = Web3()

    def sign_order(self, order: dict[str, Any]) -> str:
        try:
            order_hash = self._hash_order(order)
            message = encode_defunct(text=order_hash)
            signed_message = self.account.sign_message(message)
            return signed_message.signature.hex()
        except Exception as e:
            logger.error("order_signing_failed", error=str(e))
            raise

    def _hash_order(self, order: dict[str, Any]) -> str:
        parts = [
            str(order.get("market", "")),
            str(order.get("side", "")),
            str(order.get("size", "")),
            str(order.get("price", "")),
            str(order.get("time", "")),
            str(order.get("salt", "")),
        ]
        return ":".join(parts)

    def get_address(self) -> str:
        return self.account.address

