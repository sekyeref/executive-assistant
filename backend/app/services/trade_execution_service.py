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
        normalized_user_id = (user_id or "").strip()
        normalized_symbol = (symbol or "").strip().upper()
        normalized_side = (side or "").strip().lower()
        normalized_mode = (execution_mode or "").strip().lower()

        try:
            normalized_quantity = float(quantity)
        except (TypeError, ValueError):
            return {"status": "blocked", "reason": "Quantity must be a finite number.", "execution_mode": normalized_mode}

        if not normalized_user_id or len(normalized_user_id) > 128:
            return {"status": "blocked", "reason": "A valid user is required.", "execution_mode": normalized_mode}
        if not isinstance(portfolio_id, int) or isinstance(portfolio_id, bool) or portfolio_id <= 0:
            return {"status": "blocked", "reason": "A positive portfolio ID is required.", "execution_mode": normalized_mode}
        if not normalized_symbol or len(normalized_symbol) > 24 or not all(c.isalnum() or c in ".-" for c in normalized_symbol):
            return {"status": "blocked", "reason": "Symbol must contain only letters, numbers, dots, or hyphens.", "execution_mode": normalized_mode}
        if normalized_side not in {"buy", "sell"}:
            return {"status": "blocked", "reason": "Side must be 'buy' or 'sell'.", "execution_mode": normalized_mode}
        if normalized_mode not in {"paper", "live"}:
            return {"status": "blocked", "reason": "Execution mode must be 'paper' or 'live'.", "execution_mode": normalized_mode}
        if not math.isfinite(normalized_quantity) or normalized_quantity <= 0:
            return {"status": "blocked", "reason": "Quantity must be a finite number greater than zero.", "execution_mode": normalized_mode}
        if limit_price is not None:
            try:
                limit_price = float(limit_price)
            except (TypeError, ValueError):
                return {"status": "blocked", "reason": "Price must be a finite number greater than zero.", "execution_mode": normalized_mode}
            if not math.isfinite(limit_price) or limit_price <= 0:
                return {"status": "blocked", "reason": "Price must be a finite number greater than zero.", "execution_mode": normalized_mode}

        portfolio = self.portfolio_service.get_portfolio(portfolio_id)
        if portfolio is None or portfolio.user_id != normalized_user_id:
            return {"status": "blocked", "reason": "Portfolio not found for this user.", "execution_mode": normalized_mode}

        allowed = self.broker_service.can_execute(normalized_mode, approved)
        if not allowed:
            return {
                "status": "blocked",
                "reason": "Execution denied by guardrails.",
                "execution_mode": normalized_mode,
                "manual_confirmation_required": settings.require_manual_confirmation,
            }

        if normalized_mode == "live":
            if limit_price is None:
                return {"status": "blocked", "reason": "A positive price is required for live trade-value checks.", "execution_mode": normalized_mode}
            if normalized_quantity * limit_price > settings.max_trade_value:
                return {"status": "blocked", "reason": "Trade exceeds configured max trade value.", "max_trade_value": settings.max_trade_value}

        result = await self.broker_service.place_order(
            symbol=normalized_symbol,
            side=normalized_side,
            quantity=normalized_quantity,
            execution_mode=normalized_mode,
            approved=approved,
            order_type=order_type,
            limit_price=limit_price,
        )

        db = SessionLocal()
        try:
            db.add(TradeAuditLog(
                user_id=normalized_user_id,
                portfolio_id=portfolio_id,
                symbol=normalized_symbol,
                side=normalized_side,
                quantity=normalized_quantity,
                execution_mode=normalized_mode,
                approved=approved,
                status=result.get("status", "pending"),
                reason=result.get("reason", ""),
            ))
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

        if result.get("status") == "accepted":
            tx = self.portfolio_service.add_trade_record(
                user_id=normalized_user_id,
                portfolio_id=portfolio_id,
                symbol=normalized_symbol,
                side=normalized_side,
                quantity=normalized_quantity,
                price=result.get("limit_price") or 0.0,
                execution_mode=normalized_mode,
                status="simulated" if normalized_mode == "paper" else "pending",
                approved=approved,
                notes=notes,
            )
            return {
                "status": "ok",
                "execution_mode": normalized_mode,
                "trade_id": tx.id,
                "broker": result.get("broker", "simulated"),
                "details": result,
            }

        return result
