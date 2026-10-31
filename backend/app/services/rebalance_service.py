from __future__ import annotations

from typing import Dict, List

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import PortfolioThreshold
from app.services.market_data_service import MarketDataService
from app.services.portfolio_service import PortfolioService


class RebalanceService:
    def __init__(self, portfolio_service: PortfolioService, market_data_service: MarketDataService):
        self.portfolio_service = portfolio_service
        self.market_data_service = market_data_service

    def _get_db(self) -> Session:
        return SessionLocal()

    def set_threshold(self, user_id: str, portfolio_id: int, symbol: str, target_weight: float, tolerance: float = 0.05,
                      enabled: bool = True) -> PortfolioThreshold:
        db = self._get_db()
        try:
            existing = db.query(PortfolioThreshold).filter(
                PortfolioThreshold.user_id == user_id,
                PortfolioThreshold.portfolio_id == portfolio_id,
                PortfolioThreshold.symbol == symbol.upper(),
            ).first()

            if existing:
                existing.target_weight = target_weight
                existing.tolerance = tolerance
                existing.enabled = enabled
                db.commit()
                db.refresh(existing)
                return existing

            item = PortfolioThreshold(
                user_id=user_id,
                portfolio_id=portfolio_id,
                symbol=symbol.upper(),
                target_weight=target_weight,
                tolerance=tolerance,
                enabled=enabled,
            )
            db.add(item)
            db.commit()
            db.refresh(item)
            return item
        finally:
            db.close()

    def get_thresholds(self, user_id: str, portfolio_id: int) -> List[PortfolioThreshold]:
        db = self._get_db()
        try:
            return db.query(PortfolioThreshold).filter(
                PortfolioThreshold.user_id == user_id,
                PortfolioThreshold.portfolio_id == portfolio_id,
                PortfolioThreshold.enabled == True,
            ).all()
        finally:
            db.close()

    async def evaluate_rebalance(self, user_id: str, portfolio_id: int) -> Dict[str, object]:
        summary = await self.portfolio_service.compute_portfolio_summary(user_id, portfolio_id)
        thresholds = self.get_thresholds(user_id, portfolio_id)

        positions = summary.get("positions", [])
        total_value = float(summary.get("total_value", 0.0))

        if total_value <= 0:
            return {"portfolio_id": portfolio_id, "status": "no_data", "actions": [], "alerts": []}

        position_map = {p["symbol"].upper(): p for p in positions}
        actions = []
        alerts = []

        for threshold in thresholds:
            symbol = threshold.symbol.upper()
            current_position = position_map.get(symbol)
            if not current_position:
                continue

            current_value = float(current_position["market_value"])
            current_weight = current_value / total_value if total_value else 0.0
            target_weight = float(threshold.target_weight)
            drift = abs(current_weight - target_weight)

            if drift > threshold.tolerance:
                actions.append({
                    "symbol": symbol,
                    "current_weight": round(current_weight, 4),
                    "target_weight": round(target_weight, 4),
                    "drift": round(drift, 4),
                    "recommended_action": "buy" if current_weight < target_weight else "sell",
                    "reason": "Portfolio allocation drift exceeds tolerance band.",
                })
                alerts.append({
                    "symbol": symbol,
                    "alert_type": "allocation_drift",
                    "threshold_value": threshold.tolerance,
                    "current_value": round(current_weight, 4),
                    "target_value": round(target_weight, 4),
                })

        return {
            "portfolio_id": portfolio_id,
            "status": "ok",
            "total_value": round(total_value, 2),
            "actions": actions,
            "alerts": alerts,
        }
