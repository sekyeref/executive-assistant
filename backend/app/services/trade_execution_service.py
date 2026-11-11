from __future__ import annotations

import math
import re
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
        normalized_user_id = user_id.strip() if isinstance(user_id, str) else ""
        normalized_symbol = symbol.strip().upper() if isinstance(symbol, str) else ""
        normalized_side = side.strip().lower() if isinstance(side, str) else ""
        normalized_mode = execution_mode.strip().lower() if isinstance(execution_mode, str) else ""
        normalized_order_type = order_type.strip().lower() if isinstance(order_type, str) else ""

        try:
            normalized_quantity = float(quantity)
        except (TypeError, ValueError):
            return {"status": "blocked", "reason": "Quantity must be a finite number.", "execution_mode": normalized_mode}

        if not normalized_user_id or len(normalized_user_id) > 128:
            return {"status": "blocked", "reason": "A valid user is required.", "execution_mode": normalized_mode}
        if not isinstance(portfolio_id, int) or isinstance(portfolio_id, bool) or portfolio_id <= 0:
            return {"status": "blocked", "reason": "A positive portfolio ID is required.", "execution_mode": normalized_mode}
        if not re.fullmatch(r"[A-Z0-9][A-Z0-9.-]{0,23}", normalized_symbol):
            return {"status": "blocked", "reason": "Symbol must contain only letters, numbers, dots, or hyphens.", "execution_mode": normalized_mode}
        if normalized_side not in {"buy", "sell"}:
            return {"status": "blocked", "reason": "Side must be 'buy' or 'sell'.", "execution_mode": normalized_mode}
        if normalized_mode not in {"paper", "live"}:
            return {"status": "blocked", "reason": "Execution mode must be 'paper' or 'live'.", "execution_mode": normalized_mode}
        if normalized_order_type not in {"market", "limit"}:
            return {"status": "blocked", "reason": "Order type must be 'market' or 'limit'.", "execution_mode": normalized_mode}
        if not math.isfinite(normalized_quantity) or normalized_quantity <= 0:
            return {"status": "blocked", "reason": "Quantity must be a finite number greater than zero.", "execution_mode": normalized_mode}
        if limit_price is not None:
            try:
                limit_price = float(limit_price)
            except (TypeError, ValueError):
                return {"status": "blocked", "reason": "Price must be a finite number greater than zero.", "execution_mode": normalized_mode}
            if not math.isfinite(limit_price) or limit_price <= 0:
                return {"status": "blocked", "reason": "Price must be a finite number greater than zero.", "execution_mode": normalized_mode}
        if normalized_order_type == "limit" and limit_price is None:
            return {"status": "blocked", "reason": "A positive price is required for limit orders.", "execution_mode": normalized_mode}

        # This repository has only a simulated broker adapter. Do not let a caller
        # turn on configuration flags and accidentally treat a simulated result as live.
        if normalized_mode == "live":
            return {"status": "blocked", "reason": "Live trading is unavailable; the configured broker is simulated.", "execution_mode": normalized_mode}

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

        result = await self.broker_service.place_order(
            symbol=normalized_symbol,
            side=normalized_side,
            quantity=normalized_quantity,
            execution_mode=normalized_mode,
            approved=approved,
            order_type=normalized_order_type,
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
                status="simulated",
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
