from __future__ import annotations

from typing import Any, Dict, List


class CalendarService:
    def __init__(self):
        self.events = [
            {
                "id": "e1",
                "summary": "Executive Review",
                "start": {"dateTime": "2026-11-01T10:00:00"},
                "location": "Zoom",
            },
            {
                "id": "e2",
                "summary": "Risk Committee",
                "start": {"dateTime": "2026-11-01T14:30:00"},
                "location": "Board Room",
            },
            {
                "id": "e3",
                "summary": "Portfolio Briefing",
                "start": {"dateTime": "2026-11-02T09:15:00"},
                "location": "Executive Office",
            },
        ]

    def list_events(self) -> List[Dict[str, Any]]:
        return self.events
