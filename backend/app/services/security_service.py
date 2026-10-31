from __future__ import annotations

from app.config import settings


class SecurityService:
    def __init__(self):
        self.enabled = settings.enable_live_execution and settings.enable_real_broker

    def is_live_execution_enabled(self) -> bool:
        return bool(settings.enable_live_execution and settings.enable_real_broker)

    def approve_live_trade(self, approved: bool) -> bool:
        if not self.is_live_execution_enabled():
            return False
        if settings.require_approval_for_live and not approved:
            return False
        return True
