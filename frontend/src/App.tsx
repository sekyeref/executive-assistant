import React, { useEffect, useState } from "react";
import {
  createPortfolio,
  executeTrade,
  fetchJson,
  getMarketSnapshot,
  getMonteCarloRisk,
  getPortfolioSummary,
  getRebalanceSummary,
} from "./api";
import type { MarketItem, PortfolioSummary, RebalanceSummary, RiskSummary } from "./types";
import { NightlyBriefingWidget } from "./components/NightlyBriefingWidget";

const DEMO_USER_ID = "demo-user";
const DEMO_PORTFOLIO_ID = 1;

export default function App() {
  const [market, setMarket] = useState<MarketItem[]>([]);
  const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null);
  const [risk, setRisk] = useState<RiskSummary | null>(null);
  const [rebalance, setRebalance] = useState<RebalanceSummary | null>(null);
  const [inbox, setInbox] = useState<any[]>([]);
  const [calendar, setCalendar] = useState<any[]>([]);
  const [drafts, setDrafts] = useState<any[]>([]);
  const [brief, setBrief] = useState<any>(null);
  const [googleStatus, setGoogleStatus] = useState<string>("Not connected");
  const [subject, setSubject] = useState("Quick follow-up");
  const [body, setBody] = useState("Thanks for the update. I’ll review this and follow up shortly.");
  const [tone, setTone] = useState("professional");
  const [symbol, setSymbol] = useState("BTC-USD");
  const [side, setSide] = useState<"buy" | "sell">("buy");
  const [quantity, setQuantity] = useState("0.1");
  const [status, setStatus] = useState<string>("Ready");
  const [isLoading, setIsLoading] = useState(true);
  const [dashboardError, setDashboardError] = useState<string | null>(null);

  useEffect(() => {
    void loadDashboard();
    void checkGoogleStatus();
  }, []);

  const checkGoogleStatus = async () => {
    try {
      const result = await fetchJson<any>(`/auth/google/status?user_id=${encodeURIComponent(DEMO_USER_ID)}`);
      setGoogleStatus(result.status === "connected" ? "Connected" : "Not connected");
    } catch {
      setGoogleStatus("Not connected");
    }
  };

  const loginWithGoogle = async () => {
    try {
      const result = await fetchJson<any>(`/auth/google/login?user_id=${encodeURIComponent(DEMO_USER_ID)}`);
      window.location.href = result.auth_url;
    } catch {
      setStatus("Google login failed");
    }
  };

  const loadDashboard = async () => {
    setIsLoading(true);
    setDashboardError(null);
    const requests = await Promise.allSettled([
      getMarketSnapshot(),
      getPortfolioSummary(DEMO_USER_ID, DEMO_PORTFOLIO_ID),
      getMonteCarloRisk(DEMO_USER_ID, DEMO_PORTFOLIO_ID, 1500),
      getRebalanceSummary(DEMO_USER_ID, DEMO_PORTFOLIO_ID),
      fetchJson<any>("/api/inbox"),
      fetchJson<any>("/api/calendar/events"),
      fetchJson<any>(`/api/drafts?user_id=${encodeURIComponent(DEMO_USER_ID)}`),
      fetchJson<any>(`/api/nightly-brief?user_id=${encodeURIComponent(DEMO_USER_ID)}&portfolio_id=${DEMO_PORTFOLIO_ID}`),
    ]);
    const errors: string[] = [];
    const read = <T,>(index: number, label: string): T | undefined => {
      const result = requests[index];
      if (result.status === "fulfilled") return result.value as T;
      errors.push(label);
      return undefined;
    };

    const snapshot = read<any>(0, "market snapshot");
    if (snapshot) setMarket(Array.isArray(snapshot.items) ? snapshot.items : []);
    const summary = read<PortfolioSummary>(1, "portfolio");
    if (summary) setPortfolio(summary);
    const riskData = read<RiskSummary>(2, "risk");
    if (riskData) setRisk(riskData);
    const rebalanceData = read<RebalanceSummary>(3, "rebalance");
    if (rebalanceData) setRebalance(rebalanceData);
    const inboxData = read<any>(4, "inbox");
    if (inboxData) setInbox(Array.isArray(inboxData.messages) ? inboxData.messages : []);
    const calendarData = read<any>(5, "calendar");
    if (calendarData) setCalendar(Array.isArray(calendarData.events) ? calendarData.events : []);
    const draftData = read<any>(6, "drafts");
    if (draftData) setDrafts(Array.isArray(draftData.drafts) ? draftData.drafts : []);
    const briefData = read<any>(7, "nightly brief");
    if (briefData) setBrief(briefData);

    if (errors.length) {
      setDashboardError(`Some dashboard data could not be loaded: ${errors.join(", ")}.`);
      setStatus("Dashboard partially loaded");
    } else {
      setStatus("Dashboard ready");
    }
    setIsLoading(false);
  };

  const ensurePortfolio = async () => {
    try {
      await createPortfolio(DEMO_USER_ID, "Main Portfolio", 10000);
      await loadDashboard();
    } catch (error) {
      setDashboardError(error instanceof Error ? error.message : "Could not create portfolio.");
    }
  };

  const handleTrade = async () => {
    const parsedQuantity = Number(quantity);
    if (!symbol.trim() || !Number.isFinite(parsedQuantity) || parsedQuantity <= 0) {
      setStatus("Enter a symbol and a quantity greater than zero.");
      return;
    }
    setStatus("Submitting paper trade...");
    try {
      const result = await executeTrade(
        DEMO_USER_ID,
        DEMO_PORTFOLIO_ID,
        symbol.trim().toUpperCase(),
        side,
        parsedQuantity,
        false,
        "paper"
      );
      setStatus(result.status === "ok" ? `Paper trade recorded (ID ${result.trade_id}).` : `Trade ${result.status || "failed"}: ${result.reason || "check trade details"}`);
      await loadDashboard();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Trade failed.");
    }
  };

  const handleDraft = async () => {
    setStatus("Generating draft...");
    try {
      const result = await fetchJson<any>("/api/email-draft", {
        method: "POST",
        body: JSON.stringify({ user_id: DEMO_USER_ID, subject, body, tone, sender: "assistant@yourcompany.com" }),
      });
      await fetchJson<any>("/api/drafts", {
        method: "POST",
        body: JSON.stringify({
          user_id: DEMO_USER_ID,
          subject: result.draft.subject,
          body: result.draft.body,
          tone,
          sender: "assistant@yourcompany.com",
        }),
      });
      setStatus("Draft saved.");
      await loadDashboard();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Draft generation failed.");
    }
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div><h1>Executive Assistant</h1></div>
        <div className="topbar-actions">
          <div className="status-pill" role="status">{status}</div>
          <button className="oauth-button" onClick={loginWithGoogle}>
            {googleStatus === "Connected" ? "Google Connected" : "Connect Google"}
          </button>
          <button onClick={() => void loadDashboard()} disabled={isLoading}>
            {isLoading ? "Loading…" : "Refresh dashboard"}
          </button>
        </div>
      </header>

      {dashboardError && <p role="alert">{dashboardError}</p>}
      {isLoading && <p role="status">Loading dashboard data…</p>}

      <main className="dashboard" aria-busy={isLoading}>
        <section className="panel">
          <h2>Portfolio Overview</h2>
          {portfolio ? <>
            <div className="stat-row">
              <div className="stat-box"><label>Portfolio value</label><strong>${Number(portfolio.total_value || 0).toFixed(2)}</strong></div>
              <div className="stat-box"><label>Cash</label><strong>${Number(portfolio.cash || 0).toFixed(2)}</strong></div>
            </div>
            <table>
              <thead><tr><th>Symbol</th><th>Qty</th><th>Price</th><th>Value</th></tr></thead>
              <tbody>{(portfolio.positions || []).map((pos) => <tr key={pos.symbol}>
                <td>{pos.symbol}</td><td>{pos.quantity}</td><td>${Number(pos.market_price || 0).toFixed(2)}</td><td>${Number(pos.market_value || 0).toFixed(2)}</td>
              </tr>)}</tbody>
            </table>
          </> : <><p>{isLoading ? "Loading portfolio…" : "Portfolio unavailable."}</p><button onClick={() => void ensurePortfolio()}>Create portfolio</button></>}
        </section>

        <section className="panel"><h2>Market Snapshot</h2><div className="market-grid">
          {market.slice(0, 8).map((item) => <div key={item.symbol} className="market-card">
            <div className="market-symbol">{item.symbol}</div><div className="market-price">${Number(item.price || 0).toFixed(2)}</div>
            <div className={item.change_percent >= 0 ? "positive" : "negative"}>{item.change_percent >= 0 ? "+" : ""}{Number(item.change_percent || 0).toFixed(2)}%</div>
          </div>)}
          {!isLoading && market.length === 0 && <p>Market data unavailable.</p>}
        </div></section>

        <section className="panel"><h2>Risk</h2>{risk ? <>
          <div className="stat-row"><div className="stat-box"><label>Expected drawdown</label><strong>{Number(risk.expected_drawdown || 0).toFixed(2)}%</strong></div>
            <div className="stat-box"><label>95% VaR</label><strong>${Number(risk.var_95 || 0).toFixed(2)}</strong></div></div><p>{risk.stress_summary}</p>
        </> : <p>{isLoading ? "Loading risk data…" : "Risk data unavailable."}</p>}</section>

        <section className="panel"><h2>Rebalance</h2>{rebalance?.actions?.length ? <ul className="list">
          {rebalance.actions.map((action, idx) => <li key={`${action.symbol}-${idx}`}><strong>{action.symbol}</strong> — {action.recommended_action} ({action.current_weight * 100}% → {action.target_weight * 100}%)</li>)}
        </ul> : <p>{isLoading ? "Loading rebalance data…" : "No rebalance actions required."}</p>}</section>

        <section className="panel"><h2>Trade Execution</h2><div className="trade-form">
          <input aria-label="Symbol" value={symbol} onChange={(e) => setSymbol(e.target.value)} placeholder="Symbol" />
          <select aria-label="Side" value={side} onChange={(e) => setSide(e.target.value as "buy" | "sell")}><option value="buy">Buy</option><option value="sell">Sell</option></select>
          <input aria-label="Quantity" value={quantity} onChange={(e) => setQuantity(e.target.value)} placeholder="Qty" type="number" min="0" step="0.001" />
          <button onClick={() => void handleTrade()}>Submit Paper Trade</button>
        </div></section>

        <section className="panel"><h2>Inbox</h2><ul className="list">{inbox.map((msg) => <li key={msg.id}><strong>{msg.subject}</strong> — {msg.sender}</li>)}</ul>{!isLoading && inbox.length === 0 && <p>No inbox messages.</p>}</section>
        <section className="panel"><h2>Calendar</h2><ul className="list">{calendar.map((event) => <li key={event.id}><strong>{event.summary}</strong> — {event.location}</li>)}</ul>{!isLoading && calendar.length === 0 && <p>No calendar events.</p>}</section>

        <section className="panel wide"><h2>Draft Composer</h2><div className="draft-form">
          <input aria-label="Subject" value={subject} onChange={(e) => setSubject(e.target.value)} placeholder="Subject" />
          <select aria-label="Tone" value={tone} onChange={(e) => setTone(e.target.value)}><option value="professional">Professional</option><option value="friendly">Friendly</option><option value="concise">Concise</option><option value="assertive">Assertive</option></select>
          <textarea aria-label="Email body" value={body} onChange={(e) => setBody(e.target.value)} rows={7} placeholder="Email body" />
          <button onClick={() => void handleDraft()}>Generate &amp; Save Draft</button>
        </div></section>
        <section className="panel"><h2>Saved Drafts</h2><ul className="list">{drafts.map((draft) => <li key={draft.id}><strong>{draft.subject}</strong></li>)}</ul>{!isLoading && drafts.length === 0 && <p>No saved drafts.</p>}</section>
        {brief && <NightlyBriefingWidget data={brief} />}
      </main>
    </div>
  );
}
