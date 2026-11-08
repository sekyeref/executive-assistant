from __future__ import annotations

import math
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
        normalized_symbol = (symbol or "").strip().upper()
        normalized_side = (side or "").strip().lower()
        try:
            normalized_quantity = float(quantity)
        except (TypeError, ValueError):
            normalized_quantity = 0.0

        if not normalized_symbol:
            return {"status": "blocked", "reason": "Symbol is required.", "execution_mode": execution_mode}
        if normalized_side not in {"buy", "sell"}:
            return {"status": "blocked", "reason": "Side must be 'buy' or 'sell'.", "execution_mode": execution_mode}
        if not math.isfinite(normalized_quantity) or normalized_quantity <= 0:
            return {"status": "blocked", "reason": "Quantity must be a finite number greater than zero.", "execution_mode": execution_mode}

        if not self.broker_service.can_execute(execution_mode, approved):
            return {
                "status": "blocked",
                "reason": "Execution denied by guardrails.",
                "execution_mode": execution_mode,
                "manual_confirmation_required": settings.require_manual_confirmation,
            }

        effective_price = limit_price
        if execution_mode == "paper":
            if effective_price is None or effective_price <= 0:
                quote = await self.portfolio_service.market_data_service.get_quote(normalized_symbol)
                effective_price = float(quote["price"])
            if not math.isfinite(effective_price) or effective_price <= 0:
                return {"status": "blocked", "reason": "Could not determine a valid paper-trade price.", "execution_mode": execution_mode}
        elif limit_price is not None and quantity * limit_price > settings.max_trade_value:
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
            limit_price=effective_price,
        )
        if result.get("status") != "accepted":
            self._write_audit(user_id, portfolio_id, normalized_symbol, normalized_side, normalized_quantity,
                              execution_mode, approved, result.get("status", "blocked"), result.get("reason", ""))
            return result

        try:
            if execution_mode == "paper":
                tx = self.portfolio_service.apply_paper_trade(
                    user_id=user_id,
                    portfolio_id=portfolio_id,
                    symbol=normalized_symbol,
                    side=normalized_side,
                    quantity=normalized_quantity,
                    price=float(effective_price),
                    approved=approved,
                    notes=notes,
                )
            else:
                tx = self.portfolio_service.add_trade_record(
                    user_id=user_id,
                    portfolio_id=portfolio_id,
                    symbol=normalized_symbol,
                    side=normalized_side,
                    quantity=normalized_quantity,
                    price=float(effective_price or 0.0),
                    execution_mode=execution_mode,
                    status="pending",
                    approved=approved,
                    notes=notes,
                )
        except ValueError as exc:
            self._write_audit(user_id, portfolio_id, normalized_symbol, normalized_side, normalized_quantity,
                              execution_mode, approved, "blocked", str(exc))
            return {"status": "blocked", "reason": str(exc), "execution_mode": execution_mode}

        self._write_audit(user_id, portfolio_id, normalized_symbol, normalized_side, normalized_quantity,
                          execution_mode, approved, "accepted", "")
        return {
            "status": "ok",
            "execution_mode": execution_mode,
            "trade_id": tx.id,
            "price": float(effective_price or 0.0),
            "broker": result.get("broker", "simulated"),
            "details": result,
        }

    @staticmethod
    def _write_audit(user_id: str, portfolio_id: int, symbol: str, side: str, quantity: float,
                     execution_mode: str, approved: bool, status: str, reason: str) -> None:
        db = SessionLocal()
        try:
            db.add(TradeAuditLog(
                user_id=user_id,
                portfolio_id=portfolio_id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                execution_mode=execution_mode,
                approved=approved,
                status=status,
                reason=reason,
            ))
            db.commit()
        finally:
            db.close()
