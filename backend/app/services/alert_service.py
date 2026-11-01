from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import PortfolioAlert


class AlertService:
    def _get_db(self) -> Session:
        return SessionLocal()

    def create_alert(self, user_id: str, symbol: str, alert_type: str, threshold_value: float) -> PortfolioAlert:
        db = self._get_db()
        try:
            alert = PortfolioAlert(
                user_id=user_id,
                symbol=symbol.upper(),
                alert_type=alert_type,
                threshold_value=float(threshold_value),
                active=True,
            )
            db.add(alert)
            db.commit()
            db.refresh(alert)
            return alert
        finally:
            db.close()

    def list_alerts(self, user_id: str) -> List[PortfolioAlert]:
        db = self._get_db()
        try:
            return (
                db.query(PortfolioAlert)
                .filter(PortfolioAlert.user_id == user_id)
                .order_by(PortfolioAlert.created_at.desc())
                .all()
            )
        finally:
            db.close()
