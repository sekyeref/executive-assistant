from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Portfolio, Position, TradeTransaction
from app.services.market_data_service import MarketDataService


class PortfolioService:
    def __init__(self, market_data_service: MarketDataService):
        self.market_data_service = market_data_service

    def _get_db(self) -> Session:
        return SessionLocal()

    def create_portfolio(self, user_id: str, name: str = "Main Portfolio", cash: float = 0.0) -> Portfolio:
        db = self._get_db()
        try:
            portfolio = Portfolio(user_id=user_id, name=name, cash=cash)
            db.add(portfolio)
            db.commit()
            db.refresh(portfolio)
            return portfolio
        finally:
            db.close()

    def get_portfolio(self, portfolio_id: int) -> Optional[Portfolio]:
        db = self._get_db()
        try:
            return db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        finally:
            db.close()

    def list_portfolios(self, user_id: str) -> List[Portfolio]:
        db = self._get_db()
        try:
            return db.query(Portfolio).filter(Portfolio.user_id == user_id).order_by(Portfolio.id.asc()).all()
        finally:
            db.close()

    def get_positions(self, user_id: str, portfolio_id: int) -> List[Position]:
        db = self._get_db()
        try:
            return db.query(Position).filter(
                Position.user_id == user_id,
                Position.portfolio_id == portfolio_id,
            ).all()
        finally:
            db.close()

    def add_trade_record(self, user_id: str, portfolio_id: int, symbol: str, side: str, quantity: float, price: float,
                         execution_mode: str = "paper", status: str = "pending", approved: bool = False,
                         notes: str = "") -> TradeTransaction:
        db = self._get_db()
        try:
            tx = TradeTransaction(
                user_id=user_id,
                portfolio_id=portfolio_id,
                symbol=symbol.upper(),
                side=side.lower(),
                quantity=quantity,
                price=price,
                execution_mode=execution_mode,
                status=status,
                approved=approved,
                notes=notes,
                manual_confirmation_required=(execution_mode == "live"),
            )
            db.add(tx)
            db.commit()
            db.refresh(tx)
            return tx
        finally:
            db.close()

    def apply_paper_trade(self, user_id: str, portfolio_id: int, symbol: str, side: str, quantity: float,
                          price: float, approved: bool = True, notes: str = "") -> TradeTransaction:
        """Atomically record a simulated fill and update the portfolio's cash and position."""
        normalized_symbol = symbol.strip().upper()
        normalized_side = side.strip().lower()
        if not normalized_symbol or normalized_side not in {"buy", "sell"}:
            raise ValueError("A valid symbol and trade side are required.")
        if quantity <= 0 or price <= 0:
            raise ValueError("Quantity and execution price must be greater than zero.")

        db = self._get_db()
        try:
            portfolio = db.query(Portfolio).filter(
                Portfolio.id == portfolio_id,
                Portfolio.user_id == user_id,
            ).with_for_update().first()
            if portfolio is None:
                raise ValueError("Portfolio not found for this user.")

            position = db.query(Position).filter(
                Position.user_id == user_id,
                Position.portfolio_id == portfolio_id,
                Position.symbol == normalized_symbol,
            ).with_for_update().first()
            current_quantity = float(position.quantity or 0.0) if position else 0.0
            notional = quantity * price

            if normalized_side == "buy":
                cash = float(portfolio.cash or 0.0)
                if notional > cash:
                    raise ValueError(f"Insufficient cash: trade costs ${notional:.2f}, available cash is ${cash:.2f}.")
                new_quantity = current_quantity + quantity
                old_cost = float(position.average_cost or 0.0) * current_quantity if position else 0.0
                average_cost = (old_cost + notional) / new_quantity
                portfolio.cash = cash - notional
                if position:
                    position.quantity = new_quantity
                    position.average_cost = average_cost
                    position.market_price = price
                    position.updated_at = datetime.utcnow()
                else:
                    position = Position(
                        user_id=user_id,
                        portfolio_id=portfolio_id,
                        symbol=normalized_symbol,
                        quantity=new_quantity,
                        average_cost=average_cost,
                        market_price=price,
                    )
                    db.add(position)
            else:
                if position is None or quantity > current_quantity:
                    raise ValueError("Insufficient position quantity to sell.")
                new_quantity = current_quantity - quantity
                portfolio.cash = float(portfolio.cash or 0.0) + notional
                position.quantity = new_quantity
                position.market_price = price
                position.updated_at = datetime.utcnow()
                if new_quantity == 0:
                    position.average_cost = 0.0

            tx = TradeTransaction(
                user_id=user_id,
                portfolio_id=portfolio_id,
                symbol=normalized_symbol,
                side=normalized_side,
                quantity=quantity,
                price=price,
                execution_mode="paper",
                status="approved",
                approved=approved,
                manual_confirmation_required=False,
                notes=notes,
            )
            db.add(tx)
            db.commit()
            db.refresh(tx)
            return tx
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def upsert_position(self, user_id: str, portfolio_id: int, symbol: str, quantity: float, average_cost: float,
                        market_price: float):
        db = self._get_db()
        try:
            existing = db.query(Position).filter(
                Position.user_id == user_id,
                Position.portfolio_id == portfolio_id,
                Position.symbol == symbol.upper(),
            ).first()
            if existing:
                existing.quantity = quantity
                existing.average_cost = average_cost
                existing.market_price = market_price
                existing.updated_at = datetime.utcnow()
            else:
                db.add(Position(
                    user_id=user_id,
                    portfolio_id=portfolio_id,
                    symbol=symbol.upper(),
                    quantity=quantity,
                    average_cost=average_cost,
                    market_price=market_price,
                ))
            db.commit()
        finally:
            db.close()

    def list_transactions(self, user_id: str, portfolio_id: int) -> List[TradeTransaction]:
        db = self._get_db()
        try:
            return db.query(TradeTransaction).filter(
                TradeTransaction.user_id == user_id,
                TradeTransaction.portfolio_id == portfolio_id,
            ).order_by(TradeTransaction.created_at.desc()).all()
        finally:
            db.close()

    async def compute_portfolio_summary(self, user_id: str, portfolio_id: int) -> Dict[str, object]:
        db = self._get_db()
        try:
            portfolio = db.query(Portfolio).filter(
                Portfolio.id == portfolio_id,
                Portfolio.user_id == user_id,
            ).first()
            positions = db.query(Position).filter(
                Position.user_id == user_id,
                Position.portfolio_id == portfolio_id,
            ).all()
            if not portfolio:
                return {"portfolio_id": None, "total_value": 0.0, "cash": 0.0, "positions": []}
            cash = float(portfolio.cash or 0.0)
        finally:
            db.close()

        total_value = cash
        symbol_list = [position.symbol for position in positions]
        quote_map = {}
        if symbol_list:
            quotes = await self.market_data_service.get_quotes(symbol_list)
            quote_map = {item["symbol"]: item for item in quotes}

        rows = []
        for position in positions:
            quote = quote_map.get(position.symbol, {"price": position.market_price or 0.0})
            price = float(quote.get("price", position.market_price or 0.0))
            market_value = position.quantity * price
            total_value += market_value
            rows.append({
                "symbol": position.symbol,
                "quantity": position.quantity,
                "average_cost": position.average_cost,
                "market_price": price,
                "market_value": market_value,
                "unrealized_pnl": market_value - (position.quantity * position.average_cost),
            })

        return {
            "portfolio_id": portfolio_id,
            "portfolio_name": portfolio.name,
            "cash": cash,
            "total_value": round(total_value, 2),
            "positions": rows,
        }
