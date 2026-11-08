# Project progress

Last updated: 2026-11-08
Working branch: `fix/first-run-and-paper-trades`

## What’s working
- Backend starts on the uConsole at `http://localhost:8000`.
- Frontend starts with Vite at `http://localhost:3000` (Node.js v20.19.2, npm v9.2.0).
- Dashboard loads; the demo portfolio shows a 0.1 BTC-USD holding and updated cash/value.
- Generating and saving the `Quick follow-up` email draft is reflected in Saved Drafts.
- The user confirmed the app is running and shared full-screen dashboard screenshots.

## Code changes on this branch
Commit `8f07549` (`Fix first-run portfolio flow and apply paper trades to holdings`) updated the frontend portfolio selection/first-run flow and paper-trade handling. Paper trades use simulated market prices, update demo cash and holdings, and reject insufficient cash or sell quantity. The app remains sandbox/demo oriented; do not enable real trading as part of this flow.

## Known follow-ups
1. Update nightly briefing generation: it currently returns hard-coded portfolio value, BTC weight, risk text, and market movers that do not match the live demo portfolio.
2. Investigate risk output: the 0.1 BTC-only portfolio displayed a high expected drawdown (about 76.63% in one screenshot); validate model interpretation and presentation.
3. Run a repeatable end-to-end validation: create/select portfolio → paper trade → review risk → generate/save draft → load nightly brief. The flow has been exercised manually in part, but no automated test or CI run has verified it.
4. Review the SQLAlchemy warning about the reserved `metadata` attribute in `backend/app/models.py` when addressing task-model code.

## Local uConsole notes
- The user cloned the repository and switched to `fix/first-run-and-paper-trades`.
- Their terminal reported a local modification to `backend/app/database.py` during branch switching. Preserve it; it has not been inspected or committed remotely.
- `apt` reported an `initramfs-tools`/`dpkg` configuration failure while installing Node packages, though Node and npm were installed and the frontend subsequently started. Avoid suggesting initramfs repair unless needed; collect diagnostic output first.
- Keep backend and frontend terminals running while using the app. On the uConsole browser, use `http://localhost:3000/`.

## Accuracy notes
- Market prices are simulated by `MarketDataService` with random variation around preset demo prices; they are not live market quotes.
- Paper broker orders are simulated.
- The nightly email path currently reports a simulated send; it does not send a real email.
