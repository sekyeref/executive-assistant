from datetime import datetime
import re
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class UserScopedRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=128)

    @field_validator("user_id")
    @classmethod
    def normalize_user_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("user_id must not be blank")
        return value


class RequestEnvelope(UserScopedRequest):
    message: str = Field(..., min_length=1, max_length=10000)


class TaskCreateRequest(UserScopedRequest):
    title: str = Field(..., min_length=1, max_length=300)
    description: str = Field(default="", max_length=10000)
    priority: Literal["low", "medium", "high"] = "medium"
    due_at: Optional[datetime] = None
    source: Literal["email", "calendar", "manual", "chat"] = "manual"
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("title must not be blank")
        return value


class TaskUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=300)
    description: Optional[str] = Field(default=None, max_length=10000)
    status: Optional[Literal["todo", "in_progress", "done", "blocked"]] = None
    priority: Optional[Literal["low", "medium", "high"]] = None
    due_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class DraftCreateRequest(UserScopedRequest):
    subject: str = Field(..., min_length=1, max_length=500)
    body: str = Field(..., min_length=1, max_length=50000)
    tone: Literal["professional", "friendly", "concise", "assertive"] = "professional"
    sender: Optional[str] = Field(default=None, max_length=320)

    @field_validator("subject", "body")
    @classmethod
    def required_text_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value


class DraftUpdateRequest(BaseModel):
    subject: Optional[str] = Field(default=None, min_length=1, max_length=500)
    body: Optional[str] = Field(default=None, min_length=1, max_length=50000)
    tone: Optional[Literal["professional", "friendly", "concise", "assertive"]] = None
    status: Optional[Literal["draft", "sent"]] = None


class PortfolioCreateRequest(UserScopedRequest):
    name: str = Field(default="Main Portfolio", min_length=1, max_length=120)
    cash: float = Field(default=0.0, ge=0, allow_inf_nan=False)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("name must not be blank")
        return value


class TradeRequest(UserScopedRequest):
    portfolio_id: int = Field(..., gt=0)
    symbol: str = Field(..., min_length=1, max_length=24)
    side: Literal["buy", "sell"]
    quantity: float = Field(..., gt=0, allow_inf_nan=False)
    price: Optional[float] = Field(default=None, gt=0, allow_inf_nan=False)
    execution_mode: Literal["paper", "live"] = "paper"
    notes: str = Field(default="", max_length=2000)
    approved: bool = False
    manual_confirmation_required: bool = True

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        value = value.strip().upper()
        if not re.fullmatch(r"[A-Z0-9][A-Z0-9.-]{0,23}", value):
            raise ValueError("symbol may contain only letters, numbers, dots, and hyphens")
        return value


class AlertCreateRequest(UserScopedRequest):
    symbol: str = Field(..., min_length=1, max_length=24)
    alert_type: Literal["price_drop", "price_rise", "portfolio_drop", "threshold", "allocation_drift"]
    threshold_value: float = Field(..., gt=0, allow_inf_nan=False)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        value = value.strip().upper()
        if not re.fullmatch(r"[A-Z0-9][A-Z0-9.-]{0,23}", value):
            raise ValueError("symbol may contain only letters, numbers, dots, and hyphens")
        return value


class PortfolioThresholdRequest(UserScopedRequest):
    portfolio_id: int = Field(..., gt=0)
    symbol: str = Field(..., min_length=1, max_length=24)
    target_weight: float = Field(..., ge=0, le=1, allow_inf_nan=False)
    tolerance: float = Field(default=0.05, ge=0, le=1, allow_inf_nan=False)
    enabled: bool = True

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        value = value.strip().upper()
        if not re.fullmatch(r"[A-Z0-9][A-Z0-9.-]{0,23}", value):
            raise ValueError("symbol may contain only letters, numbers, dots, and hyphens")
        return value


class TaskCreateResponse(BaseModel):
    id: int
    user_id: str
    title: str


# Keep the datetime import available to callers that previously imported it from this module.
