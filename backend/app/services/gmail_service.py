from __future__ import annotations

from fileinput import filename
from typing import Any, Dict


class GmailService:
    def __init__(self):
        self.inbox = [
            {
                "id": "m1",
                "sender": "team@company.com",
                "subject": "Quarterly planning update",
                "snippet": "We’ve aligned on the roadmap for the next 90 days.",
                "category": "work",
            },
            {
                "id": "m2",
                "sender": "advisor@wealth.com",
                "subject": "Portfolio review",
                "snippet": "Please review the latest balance and risk summary.",
                "category": "finance",
            },
            {
                "id": "m3",
                "sender": "ops@vendor.com",
                "subject": "Invoice follow-up",
                "snippet": "We’ve sent the revised invoice for review.",
                "category": "billing",
            },
        ]

    def list_inbox(self):
        return self.inbox

    def get_message(self, message_id: str) -> Dict[str, Any]:
        for msg in self.inbox:
            if msg["id"] == message_id:
                return msg
        return {
            "id": message_id,
            "sender": "unknown",
            "subject": "No message",
            "snippet": "",
            "category": "unknown",
        }
