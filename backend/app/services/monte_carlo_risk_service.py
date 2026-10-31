from __future__ import annotations

import random
from typing import Dict

from app.services.market_data_service import MarketDataService
from app.services.portfolio_service import PortfolioService


class MonteCarloRiskService:
    def __init__(self, market_data_service: MarketDataService, portfolio_service: PortfolioService):
        self.market_data_service = market_data_service
        self.portfolio_service = portfolio_service

    async def simulate_portfolio(self, user_id: str, portfolio_id: int, scenarios: int = 2000) -> Dict[str, object]:
        summary = await self.portfolio_service.compute_portfolio_summary(user_id, portfolio_id)
        positions = summary.get("positions", [])
        total_value = float(summary.get("total_value", 0.0))

        if total_value <= 0 or not positions:
            return {
                "status": "no_data",
                "portfolio_value": 0.0,
                "expected_return": 0.0,
                "var_95": 0.0,
                "expected_drawdown": 0.0,
                "stress_summary": "No strategy data available.",
            }

        holdings = []
        for pos in positions:
            market_value = float(pos["market_value"])
            weight = market_value / total_value if total_value else 0.0
            holdings.append({
                "symbol": pos["symbol"],
                "market_value": market_value,
                "weight": weight,
                "expected_return": self._estimate_expected_return(pos["symbol"]),
                "volatility": self._estimate_volatility(pos["symbol"]),
            })

        scenario_results = []
        for _ in range(scenarios):
            simulated_value = total_value
            for holding in holdings:
                shock = random.gauss(0, holding["volatility"])
                simulated_value += (holding["market_value"] * shock) * (0.7 if holding["symbol"] == "BTC-USD" else 1.0)
            scenario_results.append(simulated_value)

        sorted_values = sorted(scenario_results)
        var_95 = total_value - sorted_values[int(len(sorted_values) * 0.05)]
        expected_return = (sum(sorted_values) / len(sorted_values)) - total_value
        expected_drawdown = max(0.0, (total_value - min(sorted_values)) / total_value) * 100

        return {
            "status": "ok",
            "portfolio_value": total_value,
            "expected_return": round(expected_return, 2),
            "var_95": round(var_95, 2),
            "expected_drawdown": round(expected_drawdown, 2),
            "stress_summary": self._build_stress_summary(expected_drawdown, var_95, total_value),
        }

    def _estimate_expected_return(self, symbol: str) -> float:
        mapping = {
            "AAPL": 0.12,
            "MSFT": 0.10,
            "NVDA": 0.18,
            "AMZN": 0.08,
            "GOOGL": 0.07,
            "TSLA": 0.16,
            "META": 0.09,
            "SPY": 0.07,
            "QQQ": 0.08,
            "BTC-USD": 0.20,
            "ETH-USD": 0.16,
            "V": 0.06,
        }
        return mapping.get(symbol, 0.08)

    def _estimate_volatility(self, symbol: str) -> float:
        mapping = {
            "AAPL": 0.22,
            "MSFT": 0.19,
            "NVDA": 0.31,
            "AMZN": 0.21,
            "GOOGL": 0.18,
            "TSLA": 0.38,
            "META": 0.27,
            "SPY": 0.12,
            "QQQ": 0.14,
            "BTC-USD": 0.42,
            "ETH-USD": 0.36,
            "V": 0.10,
        }
        return mapping.get(symbol, 0.20)

    def _build_stress_summary(self, expected_drawdown: float, var_95: float, total_value: float) -> str:
        if expected_drawdown > 18:
            return "Portfolio is highly exposed to downside volatility. Concentration risk is elevated."
        if expected_drawdown > 10:
            return "Portfolio remains moderate risk. Consider trimming concentrated exposures."
        if var_95 / total_value > 0.12:
            return "Portfolio may face significant downside in a stress event."
        return "Portfolio appears resilient under a moderate stress environment."
