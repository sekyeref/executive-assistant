from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class GoogleToken(Base):
    __tablename__ = "google_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    access_token = Column(String, nullable=True)
    refresh_token = Column(String, nullable=True)
    token_uri = Column(String, nullable=True)
    client_id = Column(String, nullable=True)
    client_secret = Column(String, nullable=True)
    scopes = Column(Text, nullable=True)
    expiry = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    status = Column(String, default="todo")
    priority = Column(String, default="medium")
    source = Column(String, default="manual")
    due_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    task_metadata = Column("metadata", JSON, default={})
    completed_at = Column(DateTime, nullable=True)


class Draft(Base):
    __tablename__ = "drafts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    tone = Column(String, default="professional")
    sender = Column(String, nullable=True)
    status = Column(String, default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    name = Column(String, default="Main Portfolio")
    cash = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    portfolio_id = Column(Integer, nullable=False)
    symbol = Column(String, nullable=False)
    quantity = Column(Float, default=0.0)
    average_cost = Column(Float, default=0.0)
    market_price = Column(Float, default=0.0)
    currency = Column(String, default="USD")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TradeTransaction(Base):
    __tablename__ = "trade_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    portfolio_id = Column(Integer, nullable=False)
    symbol = Column(String, nullable=False)
    side = Column(String, nullable=False)
    quantity = Column(Float, default=0.0)
    price = Column(Float, default=0.0)
    execution_mode = Column(String, default="paper")
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    approved = Column(Boolean, default=False)
    manual_confirmation_required = Column(Boolean, default=True)
    notes = Column(Text, default="")


class PortfolioAlert(Base):
    __tablename__ = "portfolio_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    symbol = Column(String, nullable=False)
    alert_type = Column(String, nullable=False)
    threshold_value = Column(Float, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_triggered_at = Column(DateTime, nullable=True)


class PortfolioThreshold(Base):
    __tablename__ = "portfolio_thresholds"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    portfolio_id = Column(Integer, nullable=False)
    symbol = Column(String, nullable=False)
    target_weight = Column(Float, default=0.0)
    tolerance = Column(Float, default=0.05)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TradeAuditLog(Base):
    __tablename__ = "trade_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    portfolio_id = Column(Integer, nullable=False)
    symbol = Column(String, nullable=False)
    side = Column(String, nullable=False)
    quantity = Column(Float, default=0.0)
    execution_mode = Column(String, default="paper")
    approved = Column(Boolean, default=False)
    status = Column(String, default="pending")
    reason = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
