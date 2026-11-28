#!/usr/bin/env python3
"""
Unit tests for AUREN External Risk Analytics Agent & CLI Client (Veriton)
========================================================================
Tests the client against the AUREN Risk API contract, verifying:
- Successful risk score and telemetry retrieval
- Multi-asset synthetic portfolio support
- Robust error handling (empty weights, unknown tickers, negative weights, connection failure)
- ASCII gauge rendering and report formatting
- Turnkey reproducible demo runner
- CLI argument parsing and error exits
- Mandatory analytics disclaimer presence
"""

import io
import json
import pathlib
import sys
import unittest
import urllib.request
from contextlib import redirect_stderr, redirect_stdout

# Ensure repository root and scripts directory are on sys.path
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
for path in (str(REPO_ROOT), str(SCRIPTS_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)

from engine.universe import SECTORS
from scripts.risk_client import (
    ANALYTICS_DISCLAIMER,
    EXTENDED_DISCLAIMER,
    SYNTHETIC_PORTFOLIOS,
    AurenAPIError,
    AurenClientError,
    AurenConnectionError,
    call_risk_api,
    format_comparison_report,
    format_risk_report,
    main,
    normalize_endpoint,
    render_ascii_bar,
    render_risk_gauge,
    run_demo,
    start_mock_server,
)


class TestSyntheticPortfolios(unittest.TestCase):
    """Validates the synthetic portfolio models."""

    def test_synthetic_portfolios_integrity(self):
        self.assertGreater(len(SYNTHETIC_PORTFOLIOS), 0)
        for key, p in SYNTHETIC_PORTFOLIOS.items():
            self.assertIn("name", p)
            self.assertIn("description", p)
            self.assertIn("weights", p)
            weights = p["weights"]
            self.assertIsInstance(weights, dict)
            self.assertGreater(len(weights), 0)
            self.assertGreater(sum(weights.values()), 0)
            for ticker, val in weights.items():
                self.assertIn(
                    ticker,
                    SECTORS,
                    f"Ticker '{ticker}' in preset '{key}' not in SECTORS universe",
                )
                self.assertGreater(val, 0)


class TestRiskClientAndMockServer(unittest.TestCase):
    """Tests the client communications and mock server."""

    @classmethod
    def setUpClass(cls):
        cls.server, cls.api_url = start_mock_server()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_normalize_endpoint(self):
        self.assertEqual(
            normalize_endpoint("http://localhost:8000"),
            "http://localhost:8000/risk",
        )
        self.assertEqual(
            normalize_endpoint("http://localhost:8000/"),
            "http://localhost:8000/risk",
        )
        self.assertEqual(
            normalize_endpoint("http://localhost:8000/risk"),
            "http://localhost:8000/risk",
        )

    def test_root_get_endpoint(self):
        req = urllib.request.Request(f"{self.api_url}/", method="GET")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("name", data)
            self.assertIn("disclaimer", data)
            self.assertEqual(data["disclaimer"], ANALYTICS_DISCLAIMER)

    def test_call_risk_api_success_default_preset(self):
        weights = SYNTHETIC_PORTFOLIOS["default"]["weights"]
        data = call_risk_api(endpoint=self.api_url, weights=weights)

        # Verify mandatory schema keys
        for key in (
            "score",
            "level",
            "reasons",
            "concentration",
            "volatility",
            "max_drawdown",
            "sector_exposure",
            "correlated_pairs",
            "stress",
            "disclaimer",
        ):
            self.assertIn(key, data, f"Key '{key}' missing from /risk response")

        # Verify value types and invariants
        self.assertIsInstance(data["score"], int)
        self.assertGreaterEqual(data["score"], 0)
        self.assertLessEqual(data["score"], 100)
        self.assertIn(data["level"], ["Low", "Medium", "High"])
        self.assertIsInstance(data["reasons"], list)
        self.assertIsInstance(data["concentration"], dict)
        self.assertIsInstance(data["volatility"], float)
        self.assertIsInstance(data["max_drawdown"], float)
        self.assertIsInstance(data["sector_exposure"], dict)
        self.assertIsInstance(data["stress"], dict)
        self.assertEqual(data["disclaimer"], ANALYTICS_DISCLAIMER)

        # Verify concentration details
        conc = data["concentration"]
        self.assertIn("top_asset", conc)
        self.assertIn("top_weight", conc)
        self.assertIn("effective_assets", conc)
        self.assertEqual(conc["top_asset"], "NVDA")
        self.assertAlmostEqual(conc["top_weight"], 0.40, places=2)

    def test_call_risk_api_success_balanced_preset(self):
        weights = SYNTHETIC_PORTFOLIOS["balanced"]["weights"]
        data = call_risk_api(endpoint=self.api_url, weights=weights)
        self.assertEqual(data["level"], "Low")
        self.assertEqual(data["score"], 0)
        self.assertEqual(len(data["reasons"]), 0)
        self.assertAlmostEqual(data["concentration"]["effective_assets"], 4.0, places=1)

    def test_call_risk_api_success_tech_heavy_preset(self):
        weights = SYNTHETIC_PORTFOLIOS["tech_heavy"]["weights"]
        data = call_risk_api(endpoint=self.api_url, weights=weights)
        self.assertGreaterEqual(data["score"], 65)
        self.assertEqual(data["level"], "High")
        self.assertIn("Big Tech", data["sector_exposure"])
        self.assertAlmostEqual(data["sector_exposure"]["Big Tech"], 1.0, places=2)


class TestAPIErrorHandling(unittest.TestCase):
    """Verifies that API errors are cleanly detected and wrapped."""

    @classmethod
    def setUpClass(cls):
        cls.server, cls.api_url = start_mock_server()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_empty_weights_error(self):
        with self.assertRaises(AurenAPIError) as ctx:
            call_risk_api(endpoint=self.api_url, weights={})
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Portfolio weights cannot be empty", ctx.exception.detail)

    def test_unsupported_ticker_error(self):
        with self.assertRaises(AurenAPIError) as ctx:
            call_risk_api(
                endpoint=self.api_url,
                weights={"UNKNOWN_TICKER_XYZ": 50.0, "NVDA": 50.0},
            )
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Unsupported tickers", ctx.exception.detail)

    def test_negative_weight_error(self):
        with self.assertRaises(AurenAPIError) as ctx:
            call_risk_api(
                endpoint=self.api_url,
                weights={"NVDA": -20.0, "MSFT": 40.0},
            )
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("positive numbers summing to > 0", ctx.exception.detail)

    def test_zero_sum_weights_error(self):
        with self.assertRaises(AurenAPIError) as ctx:
            call_risk_api(
                endpoint=self.api_url,
                weights={"NVDA": 0.0, "MSFT": 0.0},
            )
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("positive numbers summing to > 0", ctx.exception.detail)

    def test_endpoint_not_found_error(self):
        with self.assertRaises(AurenAPIError) as ctx:
            call_risk_api(
                endpoint=f"{self.api_url}/nonexistent_endpoint",
                weights={"NVDA": 100.0},
            )
        self.assertEqual(ctx.exception.status_code, 404)

    def test_connection_error_on_unreachable_host(self):
        # Port 54321 is presumed closed
        with self.assertRaises(AurenConnectionError) as ctx:
            call_risk_api(
                endpoint="http://127.0.0.1:54321",
                weights={"NVDA": 100.0},
                timeout=1.0,
            )
        self.assertIn("Cannot connect to AUREN Risk API", str(ctx.exception))


class TestRenderingAndFormatting(unittest.TestCase):
    """Tests ASCII progress bars, risk gauges, and report formatters."""

    def test_render_ascii_bar(self):
        self.assertEqual(render_ascii_bar(1.0, max_val=1.0, width=10), "■" * 10)
        self.assertEqual(render_ascii_bar(0.0, max_val=1.0, width=10), "░" * 10)
        half = render_ascii_bar(0.5, max_val=1.0, width=10)
        self.assertEqual(half, "■" * 5 + "░" * 5)
        self.assertEqual(render_ascii_bar(0.5, max_val=0.0, width=10), "░" * 10)

    def test_render_risk_gauge(self):
        low_gauge = render_risk_gauge(20)
        self.assertIn("[LOW RISK]", low_gauge)
        self.assertIn("20/100", low_gauge)

        med_gauge = render_risk_gauge(50)
        self.assertIn("[MEDIUM RISK]", med_gauge)
        self.assertIn("50/100", med_gauge)

        high_gauge = render_risk_gauge(85)
        self.assertIn("[HIGH RISK]", high_gauge)
        self.assertIn("85/100", high_gauge)

    def test_format_risk_report(self):
        weights = {"NVDA": 50.0, "MSFT": 50.0}
        dummy_data = {
            "score": 35,
            "level": "Medium",
            "reasons": ["Largest holding is 50% (over 30%)"],
            "concentration": {
                "top_asset": "NVDA",
                "top_weight": 0.50,
                "top3_weight": 1.0,
                "effective_assets": 2.0,
                "hhi": 0.50,
            },
            "volatility": 0.28,
            "max_drawdown": -0.25,
            "sector_exposure": {"Big Tech": 1.0},
            "correlated_pairs": [["NVDA", "MSFT", 0.75]],
            "stress": {"Big Tech falls 20%": -0.20},
            "disclaimer": ANALYTICS_DISCLAIMER,
        }

        report = format_risk_report(weights, dummy_data, portfolio_name="Test Model")
        self.assertIn("AUREN PORTFOLIO RISK REPORT", report)
        self.assertIn("Test Model", report)
        self.assertIn("NVDA", report)
        self.assertIn("MSFT", report)
        self.assertIn("35/100", report)
        self.assertIn("[MEDIUM RISK]", report)
        self.assertIn("Largest holding is 50%", report)
        self.assertIn("Big Tech", report)
        self.assertIn("NVDA <--> MSFT", report)
        self.assertIn(EXTENDED_DISCLAIMER, report)

    def test_format_comparison_report(self):
        w1 = {"NVDA": 100.0}
        d1 = {
            "score": 70,
            "level": "High",
            "volatility": 0.35,
            "max_drawdown": -0.32,
            "concentration": {"effective_assets": 1.0},
        }
        w2 = {"GLD": 50.0, "JPM": 50.0}
        d2 = {
            "score": 10,
            "level": "Low",
            "volatility": 0.15,
            "max_drawdown": -0.12,
            "concentration": {"effective_assets": 2.0},
        }

        comp = format_comparison_report("High Risk", w1, d1, "Low Risk", w2, d2)
        self.assertIn("PORTFOLIO COMPARISON", comp)
        self.assertIn("70 -> 10 (-60 pts)", comp)
        self.assertIn("De-escalation Verified", comp)
        self.assertIn(EXTENDED_DISCLAIMER, comp)


class TestCLIRunnerAndDemo(unittest.TestCase):
    """Tests the CLI main function and reproducible demo."""

    def test_run_demo_reproducible_mock(self):
        f = io.StringIO()
        with redirect_stdout(f):
            exit_code = run_demo(use_mock=True)
        out = f.getvalue()

        self.assertEqual(exit_code, 0)
        self.assertIn("REPRODUCIBLE DEMO RUNNER", out)
        self.assertIn("STEP 1: Querying High-Concentration Tech Portfolio", out)
        self.assertIn("STEP 2: Querying Diversified Cross-Sector Portfolio", out)
        self.assertIn("STEP 3: Evaluating Risk De-Escalation", out)
        self.assertIn("STEP 4: Demonstrating Robust API Error Handling", out)
        self.assertIn("ALL DEMO CHECKS PASSED", out)
        self.assertIn("0xA93ccE41173aa8CB545bE922C943726E65a8DAca", out)
        self.assertIn("USDC on Base Mainnet", out)

    def test_cli_disclaimer_flag(self):
        f = io.StringIO()
        with redirect_stdout(f):
            code = main(["--disclaimer"])
        self.assertEqual(code, 0)
        self.assertIn(EXTENDED_DISCLAIMER, f.getvalue())

    def test_cli_preset_json(self):
        f = io.StringIO()
        with redirect_stdout(f):
            code = main(["--preset", "default", "--mock", "--json"])
        self.assertEqual(code, 0)
        data = json.loads(f.getvalue())
        self.assertIn("score", data)
        self.assertIn("concentration", data)
        self.assertEqual(data["disclaimer"], ANALYTICS_DISCLAIMER)

    def test_cli_set_portfolio_arguments(self):
        f = io.StringIO()
        with redirect_stdout(f):
            code = main(
                ["--set", "NVDA=40", "MSFT=30", "ETH-USD=30", "--mock", "--json"]
            )
        self.assertEqual(code, 0)
        data = json.loads(f.getvalue())
        self.assertIn("score", data)
        self.assertGreaterEqual(data["score"], 35)

    def test_cli_weights_json_argument(self):
        f = io.StringIO()
        with redirect_stdout(f):
            code = main(
                [
                    "--weights",
                    '{"AAPL": 50, "ETH-USD": 50}',
                    "--mock",
                    "--json",
                ]
            )
        self.assertEqual(code, 0)
        data = json.loads(f.getvalue())
        self.assertEqual(data["concentration"]["top_asset"], "AAPL")

    def test_cli_error_invalid_ticker(self):
        f_err = io.StringIO()
        with redirect_stderr(f_err):
            code = main(["--set", "BADTICKER=100", "--mock"])
        self.assertEqual(code, 2)
        self.assertIn("Unsupported tickers", f_err.getvalue())

    def test_cli_error_invalid_set_syntax(self):
        f_err = io.StringIO()
        with redirect_stderr(f_err):
            code = main(["--set", "NVDA-NO-EQUALS-SIGN"])
        self.assertEqual(code, 1)
        self.assertIn("Invalid format", f_err.getvalue())

    def test_cli_error_connection_refused(self):
        f_err = io.StringIO()
        with redirect_stderr(f_err):
            code = main(["--url", "http://127.0.0.1:54321", "--preset", "default"])
        self.assertEqual(code, 3)
        self.assertIn("CONNECTION ERROR", f_err.getvalue())


if __name__ == "__main__":
    unittest.main()
