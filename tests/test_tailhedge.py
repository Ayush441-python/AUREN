import unittest
from tailhedge import TailHedge

class TestTailHedge(unittest.TestCase):
    def test_normalize_weights(self):
        raw = {"NVDA": 40, "MSFT": 60}
        norm = TailHedge.normalize_weights(raw)
        self.assertAlmostEqual(norm["NVDA"], 0.40, places=4)
        self.assertAlmostEqual(norm["MSFT"], 0.60, places=4)
        self.assertAlmostEqual(sum(norm.values()), 1.0, places=4)

    def test_normalize_weights_zero_sum_raises(self):
        with self.assertRaises(ValueError):
            TailHedge.normalize_weights({"NVDA": 0, "MSFT": 0})

    def test_calculate_hedged_weights_new_asset(self):
        initial = {"NVDA": 0.50, "AAPL": 0.50}
        # Add GLD at 20%
        hedged = TailHedge.calculate_hedged_weights(initial, hedge_asset="GLD", hedge_ratio=0.20)
        self.assertAlmostEqual(hedged["GLD"], 0.20, places=4)
        self.assertAlmostEqual(hedged["NVDA"], 0.40, places=4)
        self.assertAlmostEqual(hedged["AAPL"], 0.40, places=4)
        self.assertAlmostEqual(sum(hedged.values()), 1.0, places=4)

    def test_calculate_hedged_weights_existing_asset(self):
        initial = {"NVDA": 0.60, "GLD": 0.40}
        # Increase GLD with 10% hedge allocation
        hedged = TailHedge.calculate_hedged_weights(initial, hedge_asset="GLD", hedge_ratio=0.10)
        # Scaled NVDA = 0.6 * 0.9 = 0.54
        # Scaled GLD = 0.4 * 0.9 + 0.10 = 0.46
        self.assertAlmostEqual(hedged["NVDA"], 0.54, places=4)
        self.assertAlmostEqual(hedged["GLD"], 0.46, places=4)
        self.assertAlmostEqual(sum(hedged.values()), 1.0, places=4)

    def test_calculate_hedged_weights_invalid_ratio(self):
        with self.assertRaises(ValueError):
            TailHedge.calculate_hedged_weights({"NVDA": 1.0}, hedge_ratio=1.5)
        with self.assertRaises(ValueError):
            TailHedge.calculate_hedged_weights({"NVDA": 1.0}, hedge_ratio=-0.1)

    def test_generate_rebalancing_orders(self):
        init = {"NVDA": 0.50, "AAPL": 0.50}
        hedged = {"NVDA": 0.40, "AAPL": 0.40, "GLD": 0.20}
        orders = TailHedge.generate_rebalancing_orders(init, hedged)

        order_map = {o["ticker"]: o for o in orders}
        self.assertEqual(order_map["NVDA"]["action"], "SELL")
        self.assertAlmostEqual(order_map["NVDA"]["delta_pct"], -0.10, places=4)
        self.assertEqual(order_map["AAPL"]["action"], "SELL")
        self.assertAlmostEqual(order_map["AAPL"]["delta_pct"], -0.10, places=4)
        self.assertEqual(order_map["GLD"]["action"], "BUY")
        self.assertAlmostEqual(order_map["GLD"]["delta_pct"], +0.20, places=4)

    def test_compare_metrics(self):
        before = {
            "score": 85,
            "volatility": 0.40,
            "max_drawdown": -0.50,
            "effective_assets": 2.5,
            "stress_tests": [{"scenario_name": "Crash", "portfolio_impact": -0.30}]
        }
        after = {
            "score": 70,
            "volatility": 0.30,
            "max_drawdown": -0.35,
            "effective_assets": 3.8,
            "stress_tests": [{"scenario_name": "Crash", "portfolio_impact": -0.22}]
        }
        comp = TailHedge.compare_metrics(before, after)
        self.assertEqual(comp["score_delta"], -15)
        self.assertAlmostEqual(comp["volatility_change_pct"], -25.0, places=2)
        self.assertAlmostEqual(comp["mdd_improvement_pct"], 30.0, places=2)
        self.assertAlmostEqual(comp["effective_assets_delta"], 1.3, places=2)
        self.assertTrue(comp["is_effective"])

if __name__ == "__main__":
    unittest.main()
