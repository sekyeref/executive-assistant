export type MarketItem = {
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
};

export type Position = {
  symbol: string;
  quantity: number;
  average_cost: number;
  market_price: number;
  market_value: number;
  unrealized_pnl: number;
};

export type PortfolioSummary = {
  portfolio_id: number;
  portfolio_name: string;
  cash: number;
  total_value: number;
  positions: Position[];
};

export type RiskSummary = {
  status: string;
  portfolio_value: number;
  expected_return: number;
  var_95: number;
  expected_drawdown: number;
  stress_summary: string;
};

export type RebalanceSummary = {
  portfolio_id: number;
  status: string;
  actions: Array<{
    symbol: string;
    current_weight: number;
    target_weight: number;
    drift: number;
    recommended_action: string;
    reason: string;
  }>;
};
