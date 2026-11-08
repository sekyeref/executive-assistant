import React, { useEffect, useState } from "react";
import {
  createPortfolio,
  executeTrade,
  fetchJson,
  getMarketSnapshot,
  getMonteCarloRisk,
  getPortfolioSummary,
  getPortfolios,
  getRebalanceSummary,
} from "./api";
import type { MarketItem, PortfolioSummary, RebalanceSummary, RiskSummary } from "./types";
import { NightlyBriefingWidget } from "./components/NightlyBriefingWidget";

const DEMO_USER_ID = "demo-user";

export default function App() {
  const [market, setMarket] = useState<MarketItem[]>([]);
  const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null);
  const [portfolioId, setPortfolioId] = useState<number | null>(null);
  const [risk, setRisk] = useState<RiskSummary | null>(null);
  const [rebalance, setRebalance] = useState<RebalanceSummary | null>(null);
  const [inbox, setInbox] = useState<any[]>([]);
  const [calendar, setCalendar] = useState<any[]>([]);
  const [drafts, setDrafts] = useState<any[]>([]);
  const [brief, setBrief] = useState<any>(null);
  const [googleStatus, setGoogleStatus] = useState("Not connected");
  const [subject, setSubject] = useState("Quick follow-up");
  const [body, setBody] = useState("Thanks for the update. I’ll review this and follow up shortly.");
  const [tone, setTone] = useState("professional");
  const [symbol, setSymbol] = useState("BTC-USD");
  const [side, setSide] = useState<"buy" | "sell">("buy");
  const [quantity, setQuantity] = useState("0.1");
  const [status, setStatus] = useState("Loading dashboard...");
  const [busy, setBusy] = useState(false);

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

  const loadDashboard = async (preferredPortfolioId?: number) => {
    setBusy(true);
    try {
      const [snapshot, portfolioList] = await Promise.all([
        getMarketSnapshot(),
        getPortfolios(DEMO_USER_ID),
      ]);
      setMarket(snapshot.items || []);

      const portfolios = portfolioList.portfolios || [];
      const selected = portfolios.find((item) => item.id === preferredPortfolioId)
        || portfolios.find((item) => item.id === portfolioId)
        || portfolios[0];

      if (!selected) {
        setPortfolioId(null);
        setPortfolio(null);
        setRisk(null);
        setRebalance(null);
        setBrief(null);
        setStatus("Create a portfolio to get started");
      } else {
        setPortfolioId(selected.id);
        const [summary, riskData, rebalanceData, briefData] = await Promise.all([
          getPortfolioSummary(DEMO_USER_ID, selected.id),
          getMonteCarloRisk(DEMO_USER_ID, selected.id, 1500),
          getRebalanceSummary(DEMO_USER_ID, selected.id),
          fetchJson<any>(`/api/nightly-brief?user_id=${encodeURIComponent(DEMO_USER_ID)}&portfolio_id=${selected.id}`),
        ]);
        setPortfolio(summary.portfolio_id ? summary : null);
        setRisk(riskData);
        setRebalance(rebalanceData);
        setBrief(briefData);
        setStatus("Ready");
      }

      const [inboxData, calendarData, draftData] = await Promise.all([
        fetchJson<any>("/api/inbox"),
        fetchJson<any>("/api/calendar/events"),
        fetchJson<any>(`/api/drafts?user_id=${encodeURIComponent(DEMO_USER_ID)}`),
      ]);
      setInbox(inboxData.messages || []);
      setCalendar(calendarData.events || []);
      setDrafts(draftData.drafts || []);
    } catch (error) {
      console.error("Dashboard load failed", error);
      setStatus("Dashboard failed to load");
    } finally {
      setBusy(false);
    }
  };

  const ensurePortfolio = async () => {
    setStatus("Creating portfolio...");
    try {
      const result = await createPortfolio(DEMO_USER_ID, "Main Portfolio", 10000);
      const newPortfolioId = result.portfolio?.id;
      if (!newPortfolioId) throw new Error("Portfolio creation returned no ID");
      await loadDashboard(newPortfolioId);
    } catch (error) {
      console.error("Failed to create portfolio", error);
      setStatus("Portfolio creation failed");
    }
  };

  const handleTrade = async () => {
    if (!portfolioId) {
      setStatus("Create a portfolio before submitting a paper trade");
      return;
    }
    setStatus("Submitting paper trade...");
    try {
      const result = await executeTrade(
        DEMO_USER_ID, portfolioId, symbol, side, Number(quantity), true, "paper"
      );
      if (result.status !== "ok") {
        setStatus(`Trade ${result.status || "failed"}: ${result.reason || "Check trade details"}`);
        return;
      }
      setStatus("Paper trade recorded and portfolio updated");
      await loadDashboard(portfolioId);
    } catch (error) {
      console.error("Trade failed", error);
      setStatus("Trade failed");
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
      await loadDashboard(portfolioId ?? undefined);
    } catch (error) {
      console.error("Draft generation failed", error);
      setStatus("Draft generation failed");
    }
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div><h1>Executive Assistant</h1></div>
        <div className="topbar-actions">
          <div className="status-pill">{status}</div>
          <button className="oauth-button" onClick={loginWithGoogle}>
            {googleStatus === "Connected" ? "Google Connected" : "Connect Google"}
          </button>
        </div>
      </header>

      <main className="dashboard">
        <section className="panel">
          <h2>Portfolio Overview</h2>
          {portfolio ? (
            <>
              <div className="stat-row">
                <div className="stat-box"><label>Portfolio value</label><strong>${portfolio.total_value.toFixed(2)}</strong></div>
                <div className="stat-box"><label>Cash</label><strong>${portfolio.cash.toFixed(2)}</strong></div>
              </div>
              <table>
                <thead><tr><th>Symbol</th><th>Qty</th><th>Price</th><th>Value</th></tr></thead>
                <tbody>{(portfolio.positions || []).map((pos) => (
                  <tr key={pos.symbol}><td>{pos.symbol}</td><td>{pos.quantity}</td><td>${pos.market_price.toFixed(2)}</td><td>${pos.market_value.toFixed(2)}</td></tr>
                ))}</tbody>
              </table>
            </>
          ) : (
            <>
              <p>{busy ? "Checking for a portfolio..." : "No portfolio yet. Create one to begin the demo."}</p>
              {!busy && <button onClick={ensurePortfolio}>Create portfolio</button>}
            </>
          )}
        </section>

        <section className="panel">
          <h2>Market Snapshot</h2>
          <div className="market-grid">{market.slice(0, 8).map((item) => (
            <div key={item.symbol} className="market-card">
              <div className="market-symbol">{item.symbol}</div>
              <div className="market-price">${item.price.toFixed(2)}</div>
              <div className={item.change_percent >= 0 ? "positive" : "negative"}>{item.change_percent >= 0 ? "+" : ""}{item.change_percent.toFixed(2)}%</div>
            </div>
          ))}</div>
        </section>

        <section className="panel">
          <h2>Risk</h2>
          {risk ? <><div className="stat-row">
            <div className="stat-box"><label>Expected drawdown</label><strong>{risk.expected_drawdown.toFixed(2)}%</strong></div>
            <div className="stat-box"><label>95% VaR</label><strong>${risk.var_95.toFixed(2)}</strong></div>
          </div><p>{risk.stress_summary}</p></> : <p>{portfolio ? "Risk data unavailable." : "Create a portfolio to view risk."}</p>}
        </section>

        <section className="panel">
          <h2>Rebalance</h2>
          {rebalance?.actions?.length ? <ul className="list">{rebalance.actions.map((action, idx) => (
            <li key={`${action.symbol}-${idx}`}><strong>{action.symbol}</strong> — {action.recommended_action} ({action.current_weight * 100}% → {action.target_weight * 100}%)</li>
          ))}</ul> : <p>No rebalance actions required.</p>}
        </section>

        <section className="panel">
          <h2>Trade Execution</h2>
          <div className="trade-form">
            <input value={symbol} onChange={(e) => setSymbol(e.target.value)} placeholder="Symbol" />
            <select value={side} onChange={(e) => setSide(e.target.value as "buy" | "sell")}><option value="buy">Buy</option><option value="sell">Sell</option></select>
            <input value={quantity} onChange={(e) => setQuantity(e.target.value)} placeholder="Qty" type="number" min="0" step="0.01" />
            <button onClick={handleTrade} disabled={!portfolioId || busy}>Submit Paper Trade</button>
          </div>
        </section>

        <section className="panel"><h2>Inbox</h2><ul className="list">{inbox.map((msg) => <li key={msg.id}><strong>{msg.subject}</strong> — {msg.sender}</li>)}</ul></section>
        <section className="panel"><h2>Calendar</h2><ul className="list">{calendar.map((event) => <li key={event.id}><strong>{event.summary}</strong> — {event.location}</li>)}</ul></section>

        <section className="panel wide">
          <h2>Draft Composer</h2>
          <div className="draft-form">
            <input value={subject} onChange={(e) => setSubject(e.target.value)} placeholder="Subject" />
            <select value={tone} onChange={(e) => setTone(e.target.value)}><option value="professional">Professional</option><option value="friendly">Friendly</option><option value="concise">Concise</option><option value="assertive">Assertive</option></select>
            <textarea value={body} onChange={(e) => setBody(e.target.value)} rows={7} placeholder="Email body" />
            <button onClick={handleDraft}>Generate &amp; Save Draft</button>
          </div>
        </section>

        <section className="panel"><h2>Saved Drafts</h2><ul className="list">{drafts.map((draft) => <li key={draft.id}><strong>{draft.subject}</strong></li>)}</ul></section>
        {brief && <NightlyBriefingWidget data={brief} />}
      </main>
    </div>
  );
}
