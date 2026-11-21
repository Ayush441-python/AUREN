"""AUREN Bounty Hunter Risk Client & Dashboard Bridge.

External agent integration for AUREN Risk API (`POST /risk`).
Connects autonomous risk intelligence, portfolio stress-testing,
and terminal / dashboard visualization.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, Optional


class AurenClientError(Exception):
    """Base exception for AUREN API client errors."""


class AurenValidationError(AurenClientError):
    """Raised when portfolio weights or API input validation fails."""


class AurenAPIError(AurenClientError):
    """Raised when AUREN Risk API returns an error or invalid response."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(f"AUREN API Error [{status_code}]: {message}")
        self.status_code = status_code
        self.message = message


class AurenRiskClient:
    """Client for calling AUREN /risk endpoint from external agents or dashboards."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: float = 15.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def check_health(self) -> Dict[str, Any]:
        """Check connection and API metadata from GET /."""
        url = f"{self.base_url}/"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "AUREN-BountyHunterClient/1.0", "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data
        except Exception as e:
            raise AurenAPIError(0, f"Failed to connect to AUREN API at {url}: {e}") from e

    def analyze_portfolio(self, weights: Dict[str, float]) -> Dict[str, Any]:
        """Send portfolio weights to POST /risk and retrieve verified risk analytics."""
        if not weights:
            raise AurenValidationError("Portfolio weights cannot be empty.")

        for ticker, weight in weights.items():
            if weight <= 0:
                raise AurenValidationError(
                    f"Weight for '{ticker}' must be strictly positive (got {weight})."
                )

        payload = {"weights": {t: float(w) for t, w in weights.items()}}
        data_bytes = json.dumps(payload).encode("utf-8")
        url = f"{self.base_url}/risk"

        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={
                "User-Agent": "AUREN-BountyHunterClient/1.0",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                status_code = resp.getcode()
                raw_body = resp.read().decode("utf-8")
                res = json.loads(raw_body)
                return self._validate_response(res)
        except urllib.error.HTTPError as e:
            try:
                err_body = json.loads(e.read().decode("utf-8"))
                detail = err_body.get("detail", str(e))
            except Exception:
                detail = str(e)
            raise AurenAPIError(e.code, detail) from e
        except urllib.error.URLError as e:
            raise AurenAPIError(0, f"Network connection failed: {e.reason}") from e

    def _validate_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify the response schema contains mandatory AUREN risk fields."""
        required_fields = ["score", "level", "reasons", "concentration", "volatility", "max_drawdown"]
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise AurenAPIError(200, f"Incomplete API response contract, missing: {missing}")
        return data

    @staticmethod
    def format_terminal_report(risk_data: Dict[str, Any]) -> str:
        """Format risk analytics as a clean terminal card."""
        score = risk_data.get("score", 0)
        level = risk_data.get("level", "Unknown")
        vol = risk_data.get("volatility", 0.0)
        mdd = risk_data.get("max_drawdown", 0.0)
        conc = risk_data.get("concentration", {})
        reasons = risk_data.get("reasons", [])
        stress = risk_data.get("stress", {})

        top_asset = conc.get("top_asset", "N/A")
        top_weight = conc.get("top_weight", 0.0)
        eff_assets = conc.get("effective_assets", 0.0)

        lines = [
            "================================================================",
            "                 AUREN RISK INTELLIGENCE REPORT                 ",
            "================================================================",
            f"Risk Score : {score} / 100",
            f"Risk Level : [{level.upper()}]",
            f"Volatility : {vol:.1%} a year",
            f"Max DD     : {mdd:.1%}",
            f"Top Asset  : {top_asset} ({top_weight:.1%})",
            f"Eff. Assets: {eff_assets:.1f}",
            "----------------------------------------------------------------",
            "FLAGGED RISK FACTORS:",
        ]

        if reasons:
            for r in reasons:
                lines.append(f"  * {r}")
        else:
            lines.append("  (No high risk factor triggers hit)")

        if stress:
            lines.append("----------------------------------------------------------------")
            lines.append("STRESS SCENARIOS:")
            for sc_name, sc_impact in stress.items():
                lines.append(f"  * {sc_name:<30} : {sc_impact:+.1%}")

        lines.extend([
            "----------------------------------------------------------------",
            f"Disclaimer: {risk_data.get('disclaimer', 'Analytics only, not investment advice.')}",
            "================================================================",
        ])
        return "\n".join(lines)


def parse_weights_arg(arg: str) -> Dict[str, float]:
    """Parse JSON or key=val / key:val comma-separated weights."""
    arg = arg.strip()
    if arg.startswith("{"):
        return json.loads(arg)
    weights = {}
    for part in arg.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" in part:
            k, v = part.split(":", 1)
        elif "=" in part:
            k, v = part.split("=", 1)
        else:
            raise ValueError(f"Invalid weight format: '{part}'. Expected TICKER:WEIGHT")
        weights[k.strip()] = float(v.strip())
    return weights


def main() -> None:
    parser = argparse.ArgumentParser(description="AUREN Risk API Client & External Agent Bridge")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="Base URL for AUREN API")
    parser.add_argument("--weights", help="Portfolio weights, e.g. 'NVDA:40,MSFT:30,GOOGL:20,ETH-USD:10'")
    parser.add_argument("--demo", action="store_true", help="Run multi-portfolio stress test demo")
    parser.add_argument("--export", help="Optional file path to export JSON response")

    args = parser.parse_args()
    client = AurenRiskClient(base_url=args.url)

    if args.demo:
        demo_portfolios = {
            "Balanced Multi-Asset (Tech + Crypto)": {"NVDA": 35, "MSFT": 35, "ETH-USD": 15, "SOL-USD": 15},
            "Concentrated Semiconductor Portfolio": {"NVDA": 80, "AMD": 20},
            "Diversified Enterprise Core": {"MSFT": 30, "GOOGL": 30, "AAPL": 25, "AMZN": 15},
        }
        print("=== RUNNING AUREN RISK API MULTI-PORTFOLIO DEMO ===")
        for name, p_weights in demo_portfolios.items():
            print(f"\nEvaluating: {name}...")
            try:
                res = client.analyze_portfolio(p_weights)
                print(client.format_terminal_report(res))
            except Exception as e:
                print(f"Error evaluating {name}: {e}")
        return

    if not args.weights:
        print("Error: Must provide either --weights or --demo", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    weights = parse_weights_arg(args.weights)
    res = client.analyze_portfolio(weights)
    print(client.format_terminal_report(res))

    if args.export:
        with open(args.export, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2)
        print(f"\n[+] Exported risk report to: {args.export}")


if __name__ == "__main__":
    main()
