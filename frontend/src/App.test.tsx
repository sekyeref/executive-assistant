import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import * as api from "./api";

vi.mock("./api", () => ({
  createPortfolio: vi.fn(),
  executeTrade: vi.fn(),
  fetchJson: vi.fn(),
  getMarketSnapshot: vi.fn(),
  getMonteCarloRisk: vi.fn(),
  getPortfolioSummary: vi.fn(),
  getRebalanceSummary: vi.fn(),
}));

const mocks = vi.mocked(api);

beforeEach(() => {
  mocks.getMarketSnapshot.mockResolvedValue({ items: [{ symbol: "BTC-USD", price: 60000, change: 100, change_percent: 0.17 }] });
  mocks.getPortfolioSummary.mockResolvedValue({
    portfolio_id: 1,
    portfolio_name: "Demo Portfolio",
    cash: 1000,
    total_value: 2000,
    positions: [{ symbol: "BTC-USD", quantity: 0.01, average_cost: 59000, market_price: 60000, market_value: 600, unrealized_pnl: 10 }],
  });
  mocks.getMonteCarloRisk.mockResolvedValue({ expected_drawdown: 12.5, var_95: 200, stress_summary: "Demo risk summary" });
  mocks.getRebalanceSummary.mockResolvedValue({ portfolio_id: 1, actions: [] });
  mocks.fetchJson.mockImplementation(async (url: string) => {
    if (url.includes("/auth/google/status")) return { status: "not_connected" };
    if (url.includes("/api/inbox")) return { messages: [] };
    if (url.includes("/api/calendar/events")) return { events: [] };
    if (url.includes("/api/drafts")) return { drafts: [] };
    if (url.includes("/api/nightly-brief")) return { headline: "Demo brief", portfolio_value: 2000, btc_weight: 30, risk_summary: "Demo risk" };
    return {};
  });
});

describe("dashboard rendering", () => {
  it("renders dashboard sections and loaded portfolio/market data", async () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: "Executive Assistant" })).toBeInTheDocument();
    expect(screen.getByText("Loading dashboard data…")).toBeInTheDocument();
    expect(await screen.findByText("$2000.00")).toBeInTheDocument();
    expect(screen.getByText("BTC-USD")).toBeInTheDocument();
    for (const section of ["Portfolio Overview", "Market Snapshot", "Risk", "Rebalance", "Trade Execution", "Inbox", "Calendar", "Draft Composer", "Saved Drafts"]) {
      expect(screen.getByRole("heading", { name: section })).toBeInTheDocument();
    }
    await waitFor(() => expect(screen.getByText("Dashboard ready")).toBeInTheDocument());
  });

  it("keeps dashboard visible and reports partial failures", async () => {
    mocks.getMarketSnapshot.mockRejectedValue(new Error("backend unavailable"));
    render(<App />);
    expect(await screen.findByRole("alert")).toHaveTextContent("market snapshot");
    expect(screen.getByRole("heading", { name: "Portfolio Overview" })).toBeInTheDocument();
    expect(await screen.findByText("Dashboard partially loaded")).toBeInTheDocument();
  });

  it("shows empty states when the APIs return no records", async () => {
    mocks.getMarketSnapshot.mockResolvedValue({ items: [] });
    mocks.getPortfolioSummary.mockRejectedValue(new Error("not found"));
    render(<App />);
    expect(await screen.findByText("Market data unavailable.")).toBeInTheDocument();
    expect(screen.getByText("No inbox messages.")).toBeInTheDocument();
    expect(screen.getByText("No calendar events.")).toBeInTheDocument();
  });
});
