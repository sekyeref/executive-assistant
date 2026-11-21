import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Portfolio, Position, TradeTransaction
from app.services.portfolio_service import PortfolioService


class PaperTradeAccountingTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        self.session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.session_patch = patch("app.services.portfolio_service.SessionLocal", self.session_factory)
        self.session_patch.start()
        self.addCleanup(self.session_patch.stop)
        self.addCleanup(engine.dispose)
        self.service = PortfolioService(market_data_service=None)
        self.portfolio = self.service.create_portfolio("demo-user", cash=1000.0)
        self.portfolio_id = self.portfolio.id

    def state(self):
        portfolio = self.service.get_portfolio(self.portfolio_id)
        positions = self.service.get_positions("demo-user", self.portfolio_id)
        transactions = self.service.list_transactions("demo-user", self.portfolio_id)
        return portfolio, positions, transactions

    def test_buy_reduces_cash_creates_position_and_records_execution_price(self):
        tx = self.service.apply_paper_trade(
            "demo-user", self.portfolio_id, "btc-usd", "buy", 0.01, 60000.0,
        )

        portfolio, positions, transactions = self.state()
        self.assertAlmostEqual(portfolio.cash, 400.0)
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0].symbol, "BTC-USD")
        self.assertAlmostEqual(positions[0].quantity, 0.01)
        self.assertAlmostEqual(positions[0].average_cost, 60000.0)
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0].id, tx.id)
        self.assertEqual(transactions[0].status, "simulated")
        self.assertEqual(transactions[0].price, 60000.0)

    def test_additional_buy_uses_weighted_average_cost(self):
        self.service.apply_paper_trade("demo-user", self.portfolio_id, "BTC-USD", "buy", 0.01, 60000.0)
        self.service.apply_paper_trade("demo-user", self.portfolio_id, "BTC-USD", "buy", 0.01, 70000.0)

        portfolio, positions, transactions = self.state()
        self.assertAlmostEqual(portfolio.cash, -300.0)  # second buy is rejected; no partial mutation
        self.assertAlmostEqual(positions[0].quantity, 0.01)
        self.assertEqual(len(transactions), 1)

    def test_rejects_insufficient_cash_without_mutating_portfolio(self):
        with self.assertRaisesRegex(ValueError, "Insufficient cash"):
            self.service.apply_paper_trade("demo-user", self.portfolio_id, "BTC-USD", "buy", 0.02, 60000.0)

        portfolio, positions, transactions = self.state()
        self.assertAlmostEqual(portfolio.cash, 1000.0)
        self.assertEqual(positions, [])
        self.assertEqual(transactions, [])

    def test_sell_increases_cash_and_reduces_position(self):
        self.service.apply_paper_trade("demo-user", self.portfolio_id, "BTC-USD", "buy", 0.01, 60000.0)
        self.service.apply_paper_trade("demo-user", self.portfolio_id, "BTC-USD", "sell", 0.004, 65000.0)

        portfolio, positions, transactions = self.state()
        self.assertAlmostEqual(portfolio.cash, 660.0)
        self.assertAlmostEqual(positions[0].quantity, 0.006)
        self.assertAlmostEqual(positions[0].average_cost, 60000.0)
        self.assertEqual(len(transactions), 2)

    def test_rejects_oversell_without_mutating_portfolio(self):
        self.service.apply_paper_trade("demo-user", self.portfolio_id, "BTC-USD", "buy", 0.01, 60000.0)
        before_cash = self.service.get_portfolio(self.portfolio_id).cash

        with self.assertRaisesRegex(ValueError, "Insufficient holdings"):
            self.service.apply_paper_trade("demo-user", self.portfolio_id, "BTC-USD", "sell", 0.02, 65000.0)

        portfolio, positions, transactions = self.state()
        self.assertAlmostEqual(portfolio.cash, before_cash)
        self.assertAlmostEqual(positions[0].quantity, 0.01)
        self.assertEqual(len(transactions), 1)

    def test_rejects_trade_for_another_users_portfolio(self):
        with self.assertRaisesRegex(ValueError, "Portfolio not found"):
            self.service.apply_paper_trade("another-user", self.portfolio_id, "BTC-USD", "buy", 0.001, 60000.0)

        portfolio, positions, transactions = self.state()
        self.assertAlmostEqual(portfolio.cash, 1000.0)
        self.assertEqual(positions, [])
        self.assertEqual(transactions, [])

    def test_selling_entire_position_removes_position(self):
        self.service.apply_paper_trade("demo-user", self.portfolio_id, "BTC-USD", "buy", 0.01, 60000.0)
        self.service.apply_paper_trade("demo-user", self.portfolio_id, "BTC-USD", "sell", 0.01, 65000.0)

        portfolio, positions, transactions = self.state()
        self.assertAlmostEqual(portfolio.cash, 1050.0)
        self.assertEqual(positions, [])
        self.assertEqual(len(transactions), 2)


if __name__ == "__main__":
    unittest.main()
