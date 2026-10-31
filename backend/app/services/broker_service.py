from __future__ import annotations

from typing import Any, Dict, Optional

from app.config import settings
from app.services.security_service import SecurityService


class BrokerService:
    def __init__(self):
        self.security = SecurityService()
        self.broker = None

    def is_live_allowed(self) -> bool:
        return self.security.is_live_execution_enabled() and settings.allow_live_trading

    def can_execute(self, execution_mode: str, approved: bool = False) -> bool:
        if execution_mode == "live":
            if not self.is_live_allowed():
                return False
            if settings.require_manual_confirmation and not approved:
                return False
            return True

        if execution_mode == "paper":
            if not settings.allow_test_trading:
                return False
            return True

        return False

    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        return {"symbol": symbol.upper(), "price": 100.0, "source": "fallback", "live": False}

    async def place_order(self, symbol: str, side: str, quantity: float, execution_mode: str = "paper",
                         approved: bool = False, order_type: str = "market", limit_price: Optional[float] = None) -> Dict[str, Any]:
        if not self.can_execute(execution_mode, approved):
            return {
                "status": "blocked",
                "reason": "Execution blocked by safeguard rules.",
                "execution_mode": execution_mode,
                "approved": approved,
            }

        return {
            "status": "accepted",
            "symbol": symbol.upper(),
            "side": side.lower(),
            "quantity": quantity,
            "execution_mode": execution_mode,
            "broker": "simulated",
            "order_type": order_type,
            "limit_price": limit_price,
            "raw": {"simulated": True},
        }
