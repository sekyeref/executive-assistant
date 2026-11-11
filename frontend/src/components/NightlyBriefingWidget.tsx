import React, { useState } from "react";
import { fetchJson } from "../api";

type Props = { data: any };

export function NightlyBriefingWidget({ data }: Props) {
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const sendEmail = async () => {
    setSending(true);
    setError(null);
    try {
      const params = new URLSearchParams({ user_id: "demo-user", portfolio_id: "1", recipient: "you@example.com" });
      const payload = await fetchJson<any>(`/api/nightly-brief/send?${params}`, { method: "POST" });
      setResult(payload.email_result);
    } catch (sendError) {
      setError(sendError instanceof Error ? sendError.message : "Could not send the nightly brief.");
    } finally {
      setSending(false);
    }
  };

  if (!data) return <div>Nightly brief unavailable</div>;

  return <section className="panel">
    <h2>Nightly Briefing</h2>
    <div className="brief-header"><div><strong>{data.headline || "Portfolio briefing"}</strong></div>
      <button onClick={() => void sendEmail()} disabled={sending}>{sending ? "Sending..." : "Send Email"}</button></div>
    <div className="stat-row">
      <div className="stat-box"><label>Portfolio value</label><strong>${Number(data.portfolio_value || 0).toFixed(2)}</strong></div>
      <div className="stat-box"><label>BTC weight</label><strong>{Number(data.btc_weight || 0).toFixed(1)}%</strong></div>
    </div>
    <p>{data.risk_summary || "Risk summary unavailable."}</p>
    {error && <p role="alert">{error}</p>}
    {result && <div className="status-pill">Email: {result.status} — {result.recipient}</div>}
  </section>;
}
