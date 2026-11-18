#!/usr/bin/env python3
"""OpenBot Risk Sentinel - Autonomous Client & Intelligence Dashboard for AUREN /risk API.

This module provides a zero-dependency, production-grade external client and
terminal intelligence dashboard interface for the AUREN Risk Engine API.

Fulfills requirements of the AUREN API Integration Bounty in BOUNTY.MD:
- Connects to FastAPI endpoint `POST /risk`
- Validates contract schemas, weights, and ticker compatibility
- Renders responsive ASCII Bento intelligence cards with stress-test analytics
- Supports standalone execution, demo suites, and JSON export

Author: kushal480 (OpenBot Bounty Hunter)
License: Apache-2.0
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple


class AurenError(Exception):
    """Base exception for AUREN Sentinel client errors."""


class AurenConnectionError(AurenError):
    """Raised when connection to the AUREN API fails or times out."""


class AurenValidationError(AurenError):
    """Raised when input parameters or API validation fails (HTTP 400)."""


class AurenAPIError(AurenError):
    """Raised when the AUREN server returns a 5xx or unhandled error."""


class AurenRiskClient:
    """Client for querying the AUREN Risk Engine API with input validation and formatting."""

    DEMO_PORTFOLIOS = {
        "Balanced Multi-Asset Core": {
            "MSFT": 30.0,
            "AAPL": 30.0,
            "COST": 20.0,
            "GLD": 20.0,
        },
        "High-Beta Tech & Crypto Concentration": {
            "NVDA": 45.0,
            "ETH-USD": 35.0,
            "BTC-USD": 20.0,
        },
        "Defensive Consumer & Healthcare": {
            "COST": 35.0,
            "WMT": 35.0,
            "AMGN": 30.0,
        },
    }

    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: float = 10.0):
        """Initialize the client.

        Args:
            base_url: Base URL where the AUREN API is hosted.
            timeout: HTTP request timeout in seconds.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    @staticmethod
    def parse_weights(raw_input: str) -> Dict[str, float]:
        """Parse portfolio weights from JSON string or colon-separated pairs.

        Examples:
            '{"NVDA": 40, "MSFT": 30, "GOOGL": 20, "ETH-USD": 10}'
            'NVDA:40,MSFT:30,GOOGL:20,ETH-USD:10'
            'NVDA=40, MSFT=30, GOOGL=20'
        """
        raw_input = raw_input.strip()
        if not raw_input:
            raise AurenValidationError("Portfolio input cannot be empty.")

        # Attempt 1: Direct JSON parsing (starts with '{' or ends with '}')
        if raw_input.startswith("{") or raw_input.endswith("}"):
            try:
                data = json.loads(raw_input)
                if not isinstance(data, dict):
                    raise AurenValidationError("JSON payload must be an object/dict of ticker:weight.")
                return AurenRiskClient._sanitize_weights(data)
            except json.JSONDecodeError as err:
                raise AurenValidationError(f"Invalid JSON format for weights: {err}") from err

        # Attempt 2: Delimited key-value syntax (ticker:weight or ticker=weight)
        result: Dict[str, float] = {}
        tokens = [token.strip() for token in raw_input.split(",") if token.strip()]
        if not tokens:
            raise AurenValidationError("No valid holding tokens found in weight string.")

        for token in tokens:
            delimiter = ":" if ":" in token else ("=" if "=" in token else None)
            if not delimiter:
                raise AurenValidationError(
                    f"Invalid token '{token}'. Expected 'TICKER:WEIGHT' (e.g. 'NVDA:40')."
                )
            parts = token.split(delimiter, 1)
            ticker = parts[0].strip().upper()
            weight_str = parts[1].strip()

            if not ticker:
                raise AurenValidationError(f"Missing ticker symbol in token '{token}'.")

            try:
                weight = float(weight_str)
            except ValueError as err:
                raise AurenValidationError(
                    f"Invalid numeric weight '{weight_str}' for ticker '{ticker}'."
                ) from err

            result[ticker] = weight

        return AurenRiskClient._sanitize_weights(result)

    @staticmethod
    def _sanitize_weights(weights: Dict[str, Any]) -> Dict[str, float]:
        """Validate and sanitize parsed weights dictionary."""
        if not weights:
            raise AurenValidationError("Portfolio cannot be empty.")

        sanitized: Dict[str, float] = {}
        for k, v in weights.items():
            ticker = str(k).strip().upper()
            try:
                val = float(v)
            except (ValueError, TypeError) as err:
                raise AurenValidationError(f"Weight for '{ticker}' must be numeric, got {v!r}.") from err

            if val <= 0:
                raise AurenValidationError(
                    f"Weight for '{ticker}' must be strictly positive (> 0), got {val}."
                )
            sanitized[ticker] = val

        total_weight = sum(sanitized.values())
        if total_weight <= 0:
            raise AurenValidationError("Sum of portfolio weights must be greater than zero.")

        return sanitized

    def query_risk(self, weights: Dict[str, float]) -> Dict[str, Any]:
        """Query the /risk endpoint with portfolio weights.

        Args:
            weights: Dictionary of ticker to weight allocation.

        Returns:
            Structured risk assessment response dict.
        """
        sanitized = self._sanitize_weights(weights)
        endpoint = f"{self.base_url}/risk"
        payload = json.dumps({"weights": sanitized}).encode("utf-8")

        req = urllib.request.Request(
            endpoint,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "OpenBot-RiskSentinel/1.0",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
                data = json.loads(body)
                self._verify_contract(data)
                return data

        except urllib.error.HTTPError as err:
            err_body = err.read().decode("utf-8", errors="replace")
            detail = err_body
            try:
                parsed_json = json.loads(err_body)
                if isinstance(parsed_json, dict) and "detail" in parsed_json:
                    detail = str(parsed_json["detail"])
            except Exception:
                pass

            if err.code == 400:
                raise AurenValidationError(f"API Validation Error: {detail}") from err
            elif err.code >= 500:
                raise AurenAPIError(f"AUREN Server Error (HTTP {err.code}): {detail}") from err
            else:
                raise AurenAPIError(f"HTTP Error {err.code}: {detail}") from err

        except urllib.error.URLError as err:
            raise AurenConnectionError(
                f"Cannot connect to AUREN API at {endpoint}. Ensure server is running: {err.reason}"
            ) from err
        except json.JSONDecodeError as err:
            raise AurenAPIError(f"Received non-JSON response from {endpoint}: {err}") from err

    @staticmethod
    def _verify_contract(data: Dict[str, Any]) -> None:
        """Verify that API response satisfies the required contract fields."""
        required_fields = [
            "score",
            "level",
            "reasons",
            "concentration",
            "volatility",
            "max_drawdown",
            "sector_exposure",
            "stress",
            "disclaimer",
        ]
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise AurenAPIError(f"Response missing contract fields: {missing}")

    @staticmethod
    def render_dashboard(
        data: Dict[str, Any],
        weights: Optional[Dict[str, float]] = None,
        title: str = "AUREN RISK INTELLIGENCE REPORT",
    ) -> str:
        """Render a terminal Bento Card dashboard report."""
        score = data.get("score", 0)
        level = str(data.get("level", "UNKNOWN")).upper()
        vol = data.get("volatility", 0.0)
        mdd = data.get("max_drawdown", 0.0)
        conc = data.get("concentration", {})
        eff_assets = conc.get("effective_n", "N/A")
        top_share = conc.get("top_pct", "N/A")
        top_ticker = conc.get("top_ticker", "N/A")

        reasons: List[str] = data.get("reasons", [])
        stress_tests: Dict[str, float] = data.get("stress", {})
        sector_exp: Dict[str, float] = data.get("sector_exposure", {})
        disclaimer = data.get("disclaimer", "Analytics only, not investment advice.")

        # Formatting values
        vol_str = f"{vol * 100:.1f}% / yr" if isinstance(vol, (int, float)) else str(vol)
        mdd_str = f"{mdd * 100:.1f}%" if isinstance(mdd, (int, float)) else str(mdd)
        top_share_str = f"{top_share * 100:.1f}%" if isinstance(top_share, (int, float)) else str(top_share)
        eff_assets_str = f"{eff_assets:.1f}" if isinstance(eff_assets, (int, float)) else str(eff_assets)

        level_badge = f"[{level}]"
        bar_len = 20
        filled = int(round((score / 100.0) * bar_len))
        gauge_bar = "█" * filled + "░" * (bar_len - filled)

        lines: List[str] = [
            "================================================================================",
            f"                     {title}                     ",
            "================================================================================",
            f" Risk Score   : {score:>3} / 100  |{gauge_bar}|  Level: {level_badge}",
            f" Volatility   : {vol_str:<15} Max Drawdown      : {mdd_str}",
            f" Top Asset    : {top_ticker} ({top_share_str})  Effective Assets  : {eff_assets_str}",
            "--------------------------------------------------------------------------------",
            " PORTFOLIO WEIGHT ALLOCATION:",
        ]

        if weights:
            total = sum(weights.values())
            for ticker, w in sorted(weights.items(), key=lambda x: x[1], reverse=True):
                norm_pct = (w / total) * 100
                lines.append(f"   • {ticker:<8} : {norm_pct:>5.1f}%")
        else:
            lines.append("   (Weights not supplied to formatter)")

        lines.extend([
            "--------------------------------------------------------------------------------",
            " SECTOR / THEME EXPOSURE:",
        ])
        if sector_exp:
            for sector, pct in sorted(sector_exp.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"   • {sector:<24} : {pct * 100:>5.1f}%")
        else:
            lines.append("   • Diversified / None recorded")

        lines.extend([
            "--------------------------------------------------------------------------------",
            " MACRO STRESS SIMULATION (SCENARIO IMPACT ON PORTFOLIO):",
        ])
        if stress_tests:
            for sc_name, pnl in stress_tests.items():
                pnl_str = f"{pnl * 100:+.1f}%" if isinstance(pnl, (int, float)) else str(pnl)
                lines.append(f"   * {sc_name:<32} : {pnl_str:>7}")
        else:
            lines.append("   * No scenario stress tests configured.")

        lines.extend([
            "--------------------------------------------------------------------------------",
            " DETECTED RISK DRIVERS & PENALTIES:",
        ])
        if reasons:
            for r in reasons:
                lines.append(f"   ! {r}")
        else:
            lines.append("   ✓ No severe concentration or volatility penalties flagged.")

        lines.extend([
            "================================================================================",
            f" Notice: {disclaimer}",
            "================================================================================",
        ])

        return "\n".join(lines)


def run_demo(client: AurenRiskClient) -> int:
    """Run built-in multi-asset portfolio evaluation demo."""
    print("\n" + "=" * 80)
    print("      LAUNCHING AUREN RISK SENTINEL MULTI-PORTFOLIO INTEGRATION DEMO      ")
    print("=" * 80)

    success_count = 0
    for name, weights in client.DEMO_PORTFOLIOS.items():
        print(f"\n>>> Running Evaluation for: {name}")
        try:
            data = client.query_risk(weights)
            dashboard = client.render_dashboard(data, weights=weights, title=name.upper())
            print(dashboard)
            success_count += 1
        except AurenError as err:
            print(f"[ERROR] Failed evaluating '{name}': {err}", file=sys.stderr)

    print("\n" + "-" * 80)
    print(f"Demo completed: {success_count}/{len(client.DEMO_PORTFOLIOS)} portfolios evaluated.")
    print("-" * 80 + "\n")
    return 0 if success_count == len(client.DEMO_PORTFOLIOS) else 1


def main() -> int:
    """CLI entry point for AurenRiskClient."""
    parser = argparse.ArgumentParser(
        description="AUREN Risk Sentinel - External Client & Intelligence Dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python scripts/openbot_risk_sentinel.py --demo
  python scripts/openbot_risk_sentinel.py --weights "NVDA:40,MSFT:30,GOOGL:20,ETH-USD:10"
  python scripts/openbot_risk_sentinel.py --portfolio '{"COST": 50, "WMT": 50}' --json
  python scripts/openbot_risk_sentinel.py --weights "NVDA:60,ETH-USD:40" --export risk_report.json
""",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--demo",
        action="store_true",
        help="Run benchmark suite of multi-asset synthetic portfolios against /risk",
    )
    group.add_argument(
        "--weights",
        type=str,
        help="Comma-separated ticker:weight string (e.g. 'NVDA:40,MSFT:30,GOOGL:20,ETH-USD:10')",
    )
    group.add_argument(
        "--portfolio",
        type=str,
        help="JSON string containing portfolio weights dictionary",
    )

    parser.add_argument(
        "--api-url",
        type=str,
        default="http://127.0.0.1:8000",
        help="AUREN Risk API base URL (default: http://127.0.0.1:8000)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="HTTP request timeout in seconds (default: 10.0)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON response instead of dashboard report",
    )
    parser.add_argument(
        "--export",
        type=str,
        default=None,
        help="Export risk assessment JSON to specified output file",
    )

    args = parser.parse_args()
    client = AurenRiskClient(base_url=args.api_url, timeout=args.timeout)

    if args.demo:
        return run_demo(client)

    raw_weights = args.weights or args.portfolio
    try:
        parsed_weights = client.parse_weights(raw_weights)
        result = client.query_risk(parsed_weights)

        if args.export:
            with open(args.export, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            print(f"[Export] Report saved to {args.export}")

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(client.render_dashboard(result, weights=parsed_weights))

        return 0

    except AurenError as err:
        print(f"[AUREN Sentinel Error] {err}", file=sys.stderr)
        return 1
    except Exception as err:
        print(f"[Unexpected Error] {err}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
