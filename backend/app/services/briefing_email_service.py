from __future__ import annotations

import base64
from datetime import datetime
from email.mime.text import MIMEText
from typing import Any, Dict

from app.services.google_auth import GoogleAuthService


class BriefingEmailService:
    def __init__(self, auth_service: GoogleAuthService):
        self.auth_service = auth_service

    def build_email_body(self, brief: Dict[str, Any]) -> str:
        lines = [
            "Executive Portfolio Brief",
            f"Date: {brief.get('date', datetime.utcnow().strftime('%Y-%m-%d'))}",
            "",
            f"Headline: {brief.get('headline', 'Portfolio review summary')}",
            f"Portfolio value: ${float(brief.get('portfolio_value', 0.0)):.2f}",
            f"BTC weight: {float(brief.get('btc_weight', 0.0)):.2f}%",
            f"Portfolio health: {brief.get('portfolio_health', 'Neutral')}",
            f"Risk summary: {brief.get('risk_summary', 'No risk summary available.')}",
            "",
            "Rebalance actions:",
        ]

        actions = brief.get("rebalance_actions", [])
        if actions:
            for action in actions[:5]:
                symbol = action.get("symbol", "N/A")
                recommended = action.get("recommended_action", "review")
                current_weight = float(action.get("current_weight", 0.0)) * 100
                target_weight = float(action.get("target_weight", 0.0)) * 100
                lines.append(
                    f"- {symbol}: {recommended} ({current_weight:.1f}% -> {target_weight:.1f}%)"
                )
        else:
            lines.append("- No material drift detected.")

        lines.extend(["", "Market movers:"])
        for mover in brief.get("top_gainers", [])[:3]:
            symbol = mover.get("symbol", "N/A")
            change = float(mover.get("change_percent", 0.0))
            lines.append(f"- {symbol}: {change:.2f}%")

        lines.extend([
            "",
            "Notes:",
            "- Risk and rebalancing recommendations should be reviewed before execution.",
            "- Live trading remains disabled unless explicitly enabled.",
        ])

        return "\n".join(lines)

    def send_brief_email(self, user_id: str, recipient: str, brief: Dict[str, Any]) -> Dict[str, Any]:
        creds = self.auth_service.get_credentials(user_id)
        if not creds:
            return {"status": "blocked", "reason": "Google auth not configured for this user."}

        body = self.build_email_body(brief)
        message = MIMEText(body)
        message["To"] = recipient
        message["From"] = "me"
        message["Subject"] = f"Executive Briefing - {brief.get('date', datetime.utcnow().strftime('%Y-%m-%d'))}"

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        return {
            "status": "simulated_send",
            "message_id": "simulated",
            "recipient": recipient,
            "subject": message["Subject"],
            "raw_preview": raw[:30],
        }
