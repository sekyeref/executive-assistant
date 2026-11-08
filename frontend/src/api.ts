const API_BASE_URL = "http://localhost:8000";

export async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${url}`, {
    headers: {
      "Content-Type": "application/json",
    },
    ...options,
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function getMarketSnapshot() {
  return fetchJson<any>("/api/market/snapshot");
}

export async function getPortfolios(userId: string) {
  return fetchJson<{ portfolios: Array<{ id: number; name: string }> }>(
    `/api/portfolios?user_id=${encodeURIComponent(userId)}`
  );
}

export async function getPortfolioSummary(userId: string, portfolioId: number) {
  return fetchJson<any>(
    `/api/portfolio?user_id=${encodeURIComponent(userId)}&portfolio_id=${portfolioId}`
  );
}

export async function getMonteCarloRisk(userId: string, portfolioId: number, scenarios = 2000) {
  return fetchJson<any>(
    `/api/risk/monte-carlo?user_id=${encodeURIComponent(userId)}&portfolio_id=${portfolioId}&scenarios=${scenarios}`
  );
}

export async function getRebalanceSummary(userId: string, portfolioId: number) {
  return fetchJson<any>(
    `/api/rebalance/evaluate?user_id=${encodeURIComponent(userId)}&portfolio_id=${portfolioId}`
  );
}

export async function createPortfolio(userId: string, name: string, cash: number) {
  return fetchJson<any>("/api/portfolio", {
    method: "POST",
    body: JSON.stringify({ user_id: userId, name, cash }),
  });
}

export async function executeTrade(
  userId: string,
  portfolioId: number,
  symbol: string,
  side: "buy" | "sell",
  quantity: number,
  approved: boolean,
  executionMode: "paper" | "live" = "paper"
) {
  return fetchJson<any>("/api/trade", {
    method: "POST",
    body: JSON.stringify({
      user_id: userId,
      portfolio_id: portfolioId,
      symbol,
      side,
      quantity,
      execution_mode: executionMode,
      approved,
      notes: "UI trade request",
    }),
  });
}
