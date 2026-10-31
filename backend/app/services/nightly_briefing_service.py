from __future__ import annotations

from datetime import datetime
from typing import Any, Dict


class NightlyBriefingService:
    async def build_nightly_brief(self, user_id: str, portfolio_id: int) -> Dict[str, Any]:
        return {
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "headline": "Portfolio remains stable with modest BTC concentration risk.",
            "portfolio_value": 105000.0,
            "btc_weight": 23.4,
            "portfolio_health": "Stable",
            "risk_summary": "Risk remains moderate. BTC exposure is elevated but within the current operational band.",
            "top_gainers": [
                {"symbol": "NVDA", "change_percent": 3.2},
                {"symbol": "MSFT", "change_percent": 1.7},
                {"symbol": "AAPL", "change_percent": 1.2},
            ],
            "rebalance_actions": [
                {"symbol": "BTC-USD", "current_weight": 0.234, "target_weight": 0.15, "recommended_action": "trim"},
                {"symbol": "NVDA", "current_weight": 0.12, "target_weight": 0.10, "recommended_action": "rebalance"},
            ],
            "key_notes": [
                "Market breadth improved slightly across large-cap tech.",
                "BTC concentration remains above preferred threshold.",
                "No immediate red flags in the current risk model.",
            ],
        }
