from __future__ import annotations

from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.schemas import AlertCreateRequest, DraftCreateRequest, PortfolioCreateRequest, PortfolioThresholdRequest, TradeRequest
from app.services.alert_service import AlertService
from app.services.broker_service import BrokerService
from app.services.briefing_email_service import BriefingEmailService
from app.services.calendar_service import CalendarService
from app.services.draft_service import DraftService
from app.services.email_drafting_service import EmailDraftingService
from app.services.gmail_service import GmailService
from app.services.google_auth import GoogleAuthService
from app.services.market_data_service import MarketDataService
from app.services.monte_carlo_risk_service import MonteCarloRiskService
from app.services.nightly_briefing_service import NightlyBriefingService
from app.services.portfolio_service import PortfolioService
from app.services.rebalance_service import RebalanceService
from app.services.trade_execution_service import TradeExecutionService

Base.metadata.create_all(bind=engine)

market_data_service = MarketDataService()
portfolio_service = PortfolioService(market_data_service)
broker_service = BrokerService()
trade_execution_service = TradeExecutionService(broker_service, portfolio_service)
rebalance_service = RebalanceService(portfolio_service, market_data_service)
risk_service = MonteCarloRiskService(market_data_service, portfolio_service)
alert_service = AlertService()
gmail_service = GmailService()
calendar_service = CalendarService()
draft_service = DraftService()
email_drafting_service = EmailDraftingService()
nightly_briefing_service = NightlyBriefingService(portfolio_service, market_data_service)
google_auth_service = GoogleAuthService()
briefing_email_service = BriefingEmailService(google_auth_service)

app = FastAPI(title="Executive Assistant")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


@app.get("/auth/google/login")
def google_login(user_id: str = Query(...)):
    auth_url = google_auth_service.get_user_authorization_url()
    return {"auth_url": auth_url, "user_id": user_id}


@app.get("/auth/google/callback")
def google_callback(code: str = Query(...), state: str = Query(None)):
    if not code:
        raise HTTPException(status_code=400, detail="Missing Google auth code")

    credentials = google_auth_service.exchange_code_for_credentials(code)
    user_id = state or "demo-user"
    google_auth_service.set_credentials(user_id, credentials)
    return {"status": "authenticated", "user_id": user_id, "message": "Google auth successful"}


@app.get("/auth/google/status")
def google_status(user_id: str = Query(...)):
    creds = google_auth_service.get_credentials(user_id)
    if not creds:
        return {"status": "not_connected"}
    return {"status": "connected", "user_id": user_id}


@app.get("/api/market/quote")
async def market_quote(symbol: str):
    return await market_data_service.get_quote(symbol)


@app.get("/api/market/snapshot")
async def market_snapshot():
    return await market_data_service.get_market_snapshot()


@app.post("/api/portfolio")
def create_portfolio(payload: PortfolioCreateRequest):
    portfolio = portfolio_service.create_portfolio(
        user_id=payload.user_id,
        name=payload.name,
        cash=payload.cash,
    )
    return {"portfolio": portfolio.__dict__}


@app.get("/api/portfolios")
def list_portfolios(user_id: str = Query(...)):
    items = portfolio_service.list_portfolios(user_id)
    return {"portfolios": [item.__dict__ for item in items]}


@app.get("/api/portfolio")
async def portfolio_summary(user_id: str = Query(...), portfolio_id: int = Query(..., gt=0)):
    portfolio = portfolio_service.get_portfolio(portfolio_id)
    if portfolio is None or portfolio.user_id != user_id:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return await portfolio_service.compute_portfolio_summary(user_id, portfolio_id)


@app.get("/api/trades")
def trades(user_id: str = Query(...), portfolio_id: int = Query(..., gt=0)):
    portfolio = portfolio_service.get_portfolio(portfolio_id)
    if portfolio is None or portfolio.user_id != user_id:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    txs = portfolio_service.list_transactions(user_id, portfolio_id)
    return {"transactions": [item.__dict__ for item in txs]}


@app.post("/api/trade")
async def execute_trade(payload: TradeRequest):
    result = await trade_execution_service.execute_trade(
        user_id=payload.user_id,
        portfolio_id=payload.portfolio_id,
        symbol=payload.symbol,
        side=payload.side,
        quantity=payload.quantity,
        execution_mode=payload.execution_mode,
        approved=payload.approved,
        notes=payload.notes,
        order_type="market",
        limit_price=payload.price,
    )
    return result


@app.get("/api/risk/monte-carlo")
async def monte_carlo_risk(user_id: str = Query(...), portfolio_id: int = Query(..., gt=0), scenarios: int = Query(default=2000, ge=100, le=10000)):
    return await risk_service.simulate_portfolio(user_id, portfolio_id, scenarios=scenarios)


@app.post("/api/rebalance/threshold")
def set_threshold(payload: PortfolioThresholdRequest):
    portfolio = portfolio_service.get_portfolio(payload.portfolio_id)
    if portfolio is None or portfolio.user_id != payload.user_id:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    threshold = rebalance_service.set_threshold(
        user_id=payload.user_id,
        portfolio_id=payload.portfolio_id,
        symbol=payload.symbol,
        target_weight=payload.target_weight,
        tolerance=payload.tolerance,
        enabled=payload.enabled,
    )
    return {"threshold": threshold.__dict__}


@app.get("/api/rebalance/evaluate")
async def evaluate_rebalance(user_id: str = Query(...), portfolio_id: int = Query(..., gt=0)):
    portfolio = portfolio_service.get_portfolio(portfolio_id)
    if portfolio is None or portfolio.user_id != user_id:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return await rebalance_service.evaluate_rebalance(user_id, portfolio_id)


@app.post("/api/alerts")
def create_alert(payload: AlertCreateRequest):
    alert = alert_service.create_alert(
        user_id=payload.user_id,
        symbol=payload.symbol,
        alert_type=payload.alert_type,
        threshold_value=payload.threshold_value,
    )
    return {"alert": alert.__dict__}


@app.get("/api/alerts")
def list_alerts(user_id: str = Query(...)):
    alerts = alert_service.list_alerts(user_id)
    return {"alerts": [a.__dict__ for a in alerts]}


@app.get("/api/inbox")
def get_inbox():
    return {"messages": gmail_service.list_inbox()}


@app.get("/api/inbox/{message_id}")
def get_single_message(message_id: str):
    return gmail_service.get_message(message_id)


@app.get("/api/calendar/events")
def get_events():
    return {"events": calendar_service.list_events()}


@app.post("/api/email-draft")
def generate_email_draft(payload: DraftCreateRequest):
    draft = email_drafting_service.generate_draft(
        subject=payload.subject,
        sender=payload.sender or "assistant@yourcompany.com",
        message_body=payload.body,
        tone=payload.tone,
    )
    return {"draft": draft}


@app.post("/api/drafts")
def save_draft(payload: DraftCreateRequest):
    draft = draft_service.create_draft(
        user_id=payload.user_id,
        subject=payload.subject,
        body=payload.body,
        tone=payload.tone,
        sender=payload.sender or "assistant@yourcompany.com",
    )
    return {"draft": draft.__dict__}


@app.get("/api/drafts")
def list_drafts(user_id: str = Query(...)):
    drafts = draft_service.list_drafts(user_id)
    return {"drafts": [d.__dict__ for d in drafts]}


@app.get("/api/nightly-brief")
async def nightly_brief(user_id: str = Query(...), portfolio_id: int = Query(..., gt=0)):
    portfolio = portfolio_service.get_portfolio(portfolio_id)
    if portfolio is None or portfolio.user_id != user_id:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return await nightly_briefing_service.build_nightly_brief(user_id, portfolio_id)


@app.post("/api/nightly-brief/send")
async def send_nightly_brief(user_id: str = Query(...), portfolio_id: int = Query(..., gt=0), recipient: str = Query("you@example.com", min_length=3, max_length=320)):
    portfolio = portfolio_service.get_portfolio(portfolio_id)
    if portfolio is None or portfolio.user_id != user_id:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    brief = await nightly_briefing_service.build_nightly_brief(user_id, portfolio_id)
    email_result = briefing_email_service.send_brief_email(user_id, recipient, brief)
    return {"brief": brief, "email_result": email_result}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
