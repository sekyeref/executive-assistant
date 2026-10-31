# Executive Assistant Runbook

## 1. Setup environment
Create a `.env` file based on `.env.example`.

```bash
cp .env.example .env
```

## 2. Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

Expected:
- API on http://localhost:8000

## 3. Frontend
```bash
cd frontend
npm install
npm run dev
```

Expected:
- UI on http://localhost:3000

## 4. Validation
Check:
- `GET /health`
- `GET /api/market/snapshot`
- `GET /api/portfolio?user_id=demo-user&portfolio_id=1`
- `GET /api/risk/monte-carlo?user_id=demo-user&portfolio_id=1`
- `POST /api/trade`

## 5. Safety guardrails
This project is safe by default:
- no live execution
- no live broker usage
- no real trades unless explicitly enabled
- manual confirmation required before live actions

## 6. Auth
Google OAuth is implemented as a ready flow. Configure:
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`

Then use:
- `/auth/google/login?user_id=demo-user`

## 7. Notes
This MVP uses simulated inbox/calendar/draft data and simulated broker operations, which is suitable for safe prototyping and UI development before real API integration.
