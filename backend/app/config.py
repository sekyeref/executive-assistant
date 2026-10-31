from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Executive Assistant"
    database_url: str = "sqlite:///./assistant.db"

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"
    google_scopes: str = (
        "https://www.googleapis.com/auth/calendar "
        "https://www.googleapis.com/auth/gmail.modify "
        "https://www.googleapis.com/auth/gmail.readonly"
    )

    openai_api_key: str = ""

    autonomy_mode: str = "sandbox"
    allow_test_trading: bool = True
    allow_live_trading: bool = False
    require_manual_confirmation: bool = True
    max_trade_value: float = 1000.0

    broker_provider: str = "alpaca"
    alpaca_api_key: str = ""
    alpaca_secret_key: str = ""
    alpaca_base_url: str = "https://paper-api.alpaca.markets"
    alpaca_paper_mode: bool = True

    enable_live_execution: bool = False
    require_approval_for_live: bool = True
    enable_real_broker: bool = False

    class Config:
        case_sensitive = False


settings = Settings()
