# Executive Assistant

A safe-by-default executive assistant dashboard for:
- portfolio monitoring
- risk analysis
- strategy guidance
- paper trading
- inbox and calendar visibility
- draft generation
- nightly executive briefing

## Safety defaults
- live trading: disabled
- live broker: disabled
- paper trading: enabled
- manual approval required for live execution

## Stack
- Backend: FastAPI + SQLAlchemy
- Frontend: React + Vite
- Data model: SQLite for MVP
- Auth: Google OAuth-ready flow
- Risk model: Monte Carlo simulation

## Quick start

Backend:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

Go to:
- http://localhost:8000/health
- http://localhost:3000

## Main features
- portfolio summary
- market snapshot
- Monte Carlo risk analysis
- rebalance guidance
- paper trade execution
- Gmail/inbox mock layer
- draft generation
- nightly briefing flow
- Google OAuth-ready auth route

## Important
This project is intentionally sandbox-first and should not execute real trades without explicit approval.
