from __future__ import annotations

from typing import Any, Dict

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

from app.config import settings


class GoogleAuthService:
    def __init__(self):
        self.token_store: Dict[str, Any] = {}

    def get_credentials(self, user_id: str):
        return self.token_store.get(user_id) or None

    def set_credentials(self, user_id: str, creds: Any):
        self.token_store[user_id] = creds

    def build_oauth_flow(self):
        scopes = [scope.strip() for scope in settings.google_scopes.split(" ") if scope.strip()]
        return InstalledAppFlow.from_client_config(
            {
                "installed": {
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uris": [settings.google_redirect_uri],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                }
            },
            scopes=scopes,
        )

    def get_user_authorization_url(self):
        flow = self.build_oauth_flow()
        auth_url, _ = flow.authorization_url(prompt="consent")
        return auth_url

    def exchange_code_for_credentials(self, authorization_code: str):
        flow = self.build_oauth_flow()
        flow.fetch_token(code=authorization_code)
        return flow.credentials

    def refresh_credentials(self, user_id: str):
        creds = self.token_store.get(user_id)
        if not creds:
            return None

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            self.token_store[user_id] = creds
            return creds

        return creds
