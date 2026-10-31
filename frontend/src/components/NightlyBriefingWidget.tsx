import React, { useState } from "react";

type Props = {
  data: any;
};

export function NightlyBriefingWidget({ data }: Props) {
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState<any>(null);

  const sendEmail = async () => {
    setSending(true);
    try {
      const response = await fetch(
        "http://localhost:8000/api/nightly-brief/send?user_id=demo-user&portfolio_id=1&recipient=you@example.com",
        { method: "POST" }
      );
      const payload = await response.json();
      setResult(payload.email_result);
    } finally {
      setSending(false);
    }
  };

  if (!data) return <div>Nightly brief unavailable</div>;

  return (
    <section className="panel">
      <h2>Nightly Briefing</h2>

      <div className="brief-header">
        <div>
          <strong>{data.headline}</strong>
        </div>
        <button onClick={sendEmail} disabled={sending}>
          {sending ? "Sending..." : "Send Email"}
        </button>
      </div>

      <div className="stat-row">
        <div className="stat-box">
          <label>Portfolio value</label>
          <strong>${data.portfolio_value.toFixed(2)}</strong>
        </div>
        <div className="stat-box">
          <label>BTC weight</label>
          <strong>{data.btc_weight.toFixed(1)}%</strong>
        </div>
      </div>

      <p>{data.risk_summary}</p>

      {result && (
        <div className="status-pill">
          Email: {result.status} — {result.recipient}
        </div>
      )}
    </section>
  );
}
