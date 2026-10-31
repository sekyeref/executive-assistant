from datetime import datetime
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


class RequestEnvelope(BaseModel):
    user_id: str
    message: str


class TaskCreateRequest(BaseModel):
    user_id: str
    title: str
    description: str = ""
    priority: Literal["low", "medium", "high"] = "medium"
    due_at: Optional[datetime] = None
    source: Literal["email", "calendar", "manual", "chat"] = "manual"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[Literal["todo", "in_progress", "done", "blocked"]] = None
    priority: Optional[Literal["low", "medium", "high"]] = None
    due_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class DraftCreateRequest(BaseModel):
    user_id: str
    subject: str
    body: str
    tone: Literal["professional", "friendly", "concise", "assertive"] = "professional"
    sender: Optional[str] = None


class DraftUpdateRequest(BaseModel):
    subject: Optional[str] = None
    body: Optional[str] = None
    tone: Optional[Literal["professional", "friendly", "concise", "assertive"]] = None
    status: Optional[Literal["draft", "sent"]] = None


class PortfolioCreateRequest(BaseModel):
    user_id: str
    name: str = "Main Portfolio"
    cash: float = 0.0


class TradeRequest(BaseModel):
    user_id: str
    portfolio_id: int
    symbol: str
    side: Literal["buy", "sell"]
    quantity: float
    price: Optional[float] = None
    execution_mode: Literal["paper", "live"] = "paper"
    notes: str = ""
    approved: bool = False
    manual_confirmation_required: bool = True


class AlertCreateRequest(BaseModel):
    user_id: str
    symbol: str
    alert_type: Literal["price_drop", "price_rise", "portfolio_drop", "threshold", "allocation_drift"]
    threshold_value: float


class PortfolioThresholdRequest(BaseModel):
    user_id: str
    portfolio_id: int
    symbol: str
    target_weight: float
    tolerance: float = 0.05
    enabled: bool = True
