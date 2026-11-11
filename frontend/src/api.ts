const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

export async function fetchJson<T>(url: string, options: RequestInit = {}): Promise<T> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 8000);
  const externalSignal = options.signal;
  const abortFromExternalSignal = () => controller.abort();
  externalSignal?.addEventListener("abort", abortFromExternalSignal);

  try {
    const response = await fetch(`${API_BASE_URL}${url}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      signal: controller.signal,
    });

    const responseBody = await response.text();
    if (!response.ok) {
      let detail = responseBody;
      try {
        const parsed = JSON.parse(responseBody) as { detail?: string };
        detail = parsed.detail || responseBody;
      } catch {
        // Keep the response text when the server does not return JSON.
      }
      throw new Error(detail || `Request failed (${response.status})`);
    }

    if (!responseBody) return undefined as T;
    return JSON.parse(responseBody) as T;
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error("The API request timed out after 8 seconds.");
    }
    if (error instanceof TypeError) {
      throw new Error("Could not reach the API. Check that the backend is running and the API URL is correct.");
    }
    throw error;
  } finally {
    window.clearTimeout(timeout);
    externalSignal?.removeEventListener("abort", abortFromExternalSignal);
  }
}

export async function getMarketSnapshot() {
  return fetchJson<any>("/api/market/snapshot");
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
