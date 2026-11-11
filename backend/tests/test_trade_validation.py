import math
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from pydantic import ValidationError

from app.schemas import TradeRequest
from app.services.trade_execution_service import TradeExecutionService


class TradeRequestValidationTests(unittest.TestCase):
    def base_payload(self):
        return {
            "user_id": " demo-user ",
            "portfolio_id": 1,
            "symbol": " btc-usd ",
            "side": "buy",
            "quantity": 0.1,
        }

    def test_normalizes_user_and_symbol(self):
        request = TradeRequest(**self.base_payload())
        self.assertEqual(request.user_id, "demo-user")
        self.assertEqual(request.symbol, "BTC-USD")

    def test_rejects_invalid_numeric_inputs(self):
        for field, value in (("quantity", 0), ("quantity", -1), ("quantity", math.nan), ("price", math.inf), ("portfolio_id", 0)):
            with self.subTest(field=field, value=value):
                payload = self.base_payload()
                payload[field] = value
                with self.assertRaises(ValidationError):
                    TradeRequest(**payload)

    def test_rejects_blank_user_and_malformed_symbol(self):
        for field, value in (("user_id", "   "), ("symbol", "BTC/USD"), ("symbol", " ")):
            with self.subTest(field=field, value=value):
                payload = self.base_payload()
                payload[field] = value
                with self.assertRaises(ValidationError):
                    TradeRequest(**payload)

    def test_rejects_invalid_side_and_execution_mode(self):
        for field, value in (("side", "hold"), ("execution_mode", "real")):
            with self.subTest(field=field, value=value):
                payload = self.base_payload()
                payload[field] = value
                with self.assertRaises(ValidationError):
                    TradeRequest(**payload)


class TradeExecutionOwnershipTests(unittest.IsolatedAsyncioTestCase):
    def make_service(self, portfolio):
        broker = Mock()
        broker.can_execute.return_value = True
        broker.place_order = AsyncMock(return_value={"status": "accepted"})
        portfolios = Mock()
        portfolios.get_portfolio.return_value = portfolio
        service = TradeExecutionService(broker, portfolios)
        return service, broker, portfolios

    async def test_blocks_missing_or_foreign_portfolio_before_broker_call(self):
        for portfolio in (None, SimpleNamespace(user_id="other-user")):
            with self.subTest(portfolio=portfolio):
                service, broker, portfolios = self.make_service(portfolio)
                result = await service.execute_trade("demo-user", 1, "BTC-USD", "buy", 0.1)
                self.assertEqual(result["status"], "blocked")
                self.assertIn("Portfolio not found", result["reason"])
                broker.can_execute.assert_not_called()
                broker.place_order.assert_not_awaited()
                portfolios.add_trade_record.assert_not_called()

    async def test_blocks_non_finite_quantity_without_portfolio_or_broker(self):
        service, broker, portfolios = self.make_service(SimpleNamespace(user_id="demo-user"))
        result = await service.execute_trade("demo-user", 1, "BTC-USD", "buy", math.inf)
        self.assertEqual(result["status"], "blocked")
        self.assertIn("finite", result["reason"])
        portfolios.get_portfolio.assert_not_called()
        broker.can_execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
