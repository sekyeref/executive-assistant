# Executive Assistant Cheat Sheet

## 1) Start backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python -m app.main
```

## 2) Start frontend
```bash
cd frontend
npm install
npm run dev
```

## 3) Open app
- http://localhost:3000

## 4) Create portfolio
- Click "Create portfolio" in the UI
or
```bash
curl -X POST http://localhost:8000/api/portfolio \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo-user","name":"Main Portfolio","cash":10000}'
```

## 5) Paper trade
Use in the UI:
- Symbol: BTC-USD
- Side: buy
- Quantity: 0.1
- Click: Submit Paper Trade

## 6) Check risk
Open the risk card to view:
- expected drawdown
- 95% VaR
- stress summary

## 7) Rebalance suggestions
The rebalance panel shows drift and recommended action.

## 8) Draft email
In the draft composer:
- pick a tone
- write a short note
- click: Generate & Save Draft

## 9) Nightly brief
Click the button inside the nightly briefing widget to send a simulated summary email.

## 10) Safety rules
- live trading is disabled by default
- real broker execution is off
- this is sandbox mode only

## 11) Main endpoints
- http://localhost:8000/health
- http://localhost:8000/api/market/snapshot
- http://localhost:8000/api/portfolio?user_id=demo-user&portfolio_id=1
- http://localhost:8000/api/risk/monte-carlo?user_id=demo-user&portfolio_id=1

## 12) Included features
- market snapshot
- portfolio summary
- risk simulation
- rebalancing
- safe paper trades
- inbox
- calendar
- email drafting
- nightly briefing

## 13) Best first demo sequence
1. create portfolio
2. submit paper trade
3. review risk
4. generate draft
5. send nightly brief

## 14) Use notes
This MVP is intentionally safe and demo-friendly. It is built as a strong foundation for future real API integration.
