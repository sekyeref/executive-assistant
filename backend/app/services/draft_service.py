from __future__ import annotations

from datetime import datetime
from typing import List

from app.database import SessionLocal
from app.models import Draft


class DraftService:
    def create_draft(self, user_id: str, subject: str, body: str, tone: str = "professional", sender: str = None) -> Draft:
        db = SessionLocal()
        draft = Draft(
            user_id=user_id,
            subject=subject,
            body=body,
            tone=tone,
            sender=sender,
            status="draft",
            created_at=datetime.utcnow(),
        )
        db.add(draft)
        db.commit()
        db.refresh(draft)
        db.close()
        return draft

    def list_drafts(self, user_id: str) -> List[Draft]:
        db = SessionLocal()
        try:
            return db.query(Draft).filter(Draft.user_id == user_id).order_by(Draft.created_at.desc()).all()
        finally:
            db.close()
