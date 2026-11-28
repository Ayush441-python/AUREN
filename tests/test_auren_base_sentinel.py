#!/usr/bin/env python3
import unittest
import json
import urllib.request
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
from auren_base_sentinel import (
    start_mock_server,
    query_auren_risk,
    resolve_base_wallet,
    compute_defensive_rebalance,
    DEFAULT_BASE_RPC,
    DEFENSIVE_ASSETS
)

class TestAurenBaseSentinel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server, cls.api_url = start_mock_server(port=8911)

    def test_mock_server_empty_weights(self):
        req = urllib.request.Request(
            self.api_url,
            data=json.dumps({"weights": {}}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 400)

    def test_query_auren_risk_high_risk(self):
        portfolio = {"NVDA": 60.0, "ETH-USD": 40.0}
        res = query_auren_risk(self.api_url, portfolio)
        self.assertIn("score", res)
        self.assertIn("level", res)
        self.assertGreaterEqual(res["score"], 35)
        self.assertIn("concentration", res)
        self.assertIn("stress", res)

    def test_resolve_base_wallet(self):
        wallet = "0x759797593fed8f313d8fdba7a3a0d491f0e4b9f7"
        holdings = resolve_base_wallet(wallet)
        self.assertIsInstance(holdings, dict)
        self.assertGreater(len(holdings), 0)
        self.assertIn("ETH-USD", holdings)

    def test_invalid_wallet_address(self):
        with self.assertRaises(ValueError):
            resolve_base_wallet("invalid_address")

    def test_compute_defensive_rebalance(self):
        risky_portfolio = {"NVDA": 70.0, "ETH-USD": 30.0}
        rebalanced = compute_defensive_rebalance(risky_portfolio)
        self.assertIsInstance(rebalanced, dict)
        # All individual weights should be <= 25%
        for ticker, wt in rebalanced.items():
            self.assertLessEqual(wt, 25.0)
        # Re-evaluating rebalanced portfolio with AUREN mock should reduce risk score
        res = query_auren_risk(self.api_url, rebalanced)
        self.assertLess(res["score"], 35)
        self.assertEqual(res["level"], "Low")

if __name__ == "__main__":
    unittest.main()
