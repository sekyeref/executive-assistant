from __future__ import annotations

import re
from typing import Any, Dict


class EmailDraftingService:
    def __init__(self):
        self.templates = {
            "professional": "Hi {name},\n\nThank you for your update. I appreciate the progress and will review the next steps shortly.\n\nBest regards,\n{sender}",
            "friendly": "Hi {name},\n\nThanks again for the update. This is really helpful, and I’ll keep things moving from here.\n\nThanks,\n{sender}",
            "concise": "Hi {name},\n\nThanks for the update. I’ll review this and follow up shortly.\n\nBest,\n{sender}",
            "assertive": "Hi {name},\n\nThank you for the update. I’ve reviewed the details and would like to move forward with the next step promptly.\n\nRegards,\n{sender}",
        }

    def generate_draft(self, subject: str, sender: str, message_body: str, tone: str = "professional") -> Dict[str, Any]:
        name_match = re.search(r"from\s+([A-Za-z .'-]+)", message_body, re.IGNORECASE)
        recipient_name = name_match.group(1).strip() if name_match else "there"

        body = self.templates.get(tone, self.templates["professional"]).format(
            name=recipient_name,
            sender=sender,
        )

        return {
            "subject": subject or "Follow-up",
            "body": body,
            "tone": tone,
            "sender": sender,
            "status": "draft",
        }
