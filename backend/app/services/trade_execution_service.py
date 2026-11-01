from __future__ import annotations

from typing import Any, Dict, Optional

from app.config import settings
from app.database import SessionLocal
from app.models import TradeAuditLog
from app.services.broker_service import BrokerService
from app.services.portfolio_service import PortfolioService


class TradeExecutionService:
    def __init__(self, broker_service: BrokerService, portfolio_service: PortfolioService):
        self.broker_service = broker_service
        self.portfolio_service = portfolio_service

    async def execute_trade(self, user_id: str, portfolio_id: int, symbol: str, side: str, quantity: float,
                            execution_mode: str = "paper", approved: bool = False, notes: str = "",
                            order_type: str = "market", limit_price: Optional[float] = None) -> Dict[str, Any]:
        normalized_symbol = (symbol or "").strip()
        normalized_side = (side or "").strip().lower()
        normalized_quantity = float(quantity or 0.0)

        if not normalized_symbol:
            return {"status": "blocked", "reason": "Symbol is required.", "execution_mode": execution_mode}

        if normalized_side not in {"buy", "sell"}:
            return {"status": "blocked", "reason": "Side must be 'buy' or 'sell'.", "execution_mode": execution_mode}

        if normalized_quantity <= 0:
            return {"status": "blocked", "reason": "Quantity must be greater than zero.", "execution_mode": execution_mode}

        allowed = self.broker_service.can_execute(execution_mode, approved)
        if not allowed:
            return {
                "status": "blocked",
                "reason": "Execution denied by guardrails.",
                "execution_mode": execution_mode,
                "manual_confirmation_required": settings.require_manual_confirmation,
            }

        if float(quantity) * float(limit_price or 0.0) > settings.max_trade_value and execution_mode == "live":
            return {
                "status": "blocked",
                "reason": "Trade exceeds configured max trade value.",
                "max_trade_value": settings.max_trade_value,
            }

        result = await self.broker_service.place_order(
            symbol=normalized_symbol,
            side=normalized_side,
            quantity=normalized_quantity,
            execution_mode=execution_mode,
            approved=approved,
            order_type=order_type,
            limit_price=limit_price,
        )

        db = SessionLocal()
        db.add(TradeAuditLog(
            user_id=user_id,
            portfolio_id=portfolio_id,
            symbol=normalized_symbol.upper(),
            side=normalized_side,
            quantity=normalized_quantity,
            execution_mode=execution_mode,
            approved=approved,
            status=result.get("status", "pending"),
            reason=result.get("reason", ""),
        ))
        db.commit()
        db.close()

        if result.get("status") == "accepted":
            tx = self.portfolio_service.add_trade_record(
                user_id=user_id,
                portfolio_id=portfolio_id,
                symbol=normalized_symbol,
                side=normalized_side,
                quantity=normalized_quantity,
                price=result.get("limit_price") or 0.0,
                execution_mode=execution_mode,
                status="approved" if execution_mode == "paper" else "pending",
                approved=approved,
                notes=notes,
            )
            return {
                "status": "ok",
                "execution_mode": execution_mode,
                "trade_id": tx.id,
                "broker": result.get("broker", "simulated"),
                "details": result,
            }

        return result
