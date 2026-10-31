from __future__ import annotations

import random
from typing import Any, Dict, List


class MarketDataService:
    def __init__(self):
        self.demo_prices = {
            "AAPL": 214.53,
            "MSFT": 432.84,
            "NVDA": 130.41,
            "AMZN": 181.31,
            "GOOGL": 171.98,
            "TSLA": 241.11,
            "META": 517.28,
            "SPY": 541.41,
            "QQQ": 474.20,
            "V": 274.88,
            "BTC-USD": 61240.15,
            "ETH-USD": 3375.82,
        }

    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        symbol = symbol.upper()
        base = self.demo_prices.get(symbol, 100.0)
        drift = random.uniform(-0.03, 0.03)
        price = round(base * (1 + drift), 2)
        return {
            "symbol": symbol,
            "price": price,
            "previous_close": round(base, 2),
            "change": round(price - base, 2),
            "change_percent": round(((price - base) / base) * 100, 2),
            "currency": "USD",
        }

    async def get_quotes(self, symbols: List[str]) -> List[Dict[str, Any]]:
        results = []
        for symbol in symbols:
            results.append(await self.get_quote(symbol))
        return results

    async def get_market_snapshot(self) -> Dict[str, List[Dict[str, Any]]]:
        symbols = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "TSLA", "META", "SPY", "QQQ", "BTC-USD", "ETH-USD"]
        return {"items": await self.get_quotes(symbols)}
