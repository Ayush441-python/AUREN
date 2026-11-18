#!/usr/bin/env python3
"""
Auren Risk Client - Bounty Hunter Autonomous Agent & Multi-Asset Risk Sentinel.
Standard-library zero-dependency client connecting multi-asset portfolios to AUREN /risk.
"""

from __future__ import annotations

import argparse
import json
import socket
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Union

REQUIRED_CONTRACT_FIELDS: List[str] = [
    "score",
    "level",
    "reasons",
    "concentration",
    "volatility",
    "max_drawdown",
    "sector_exposure",
    "stress",
]


class AurenClientError(Exception):
    """Base exception for Auren Risk Client."""
    pass


class AurenAPIError(AurenClientError):
    """Raised when Auren API returns HTTP 4xx or 5xx."""

    def __init__(self, status_code: int, detail: str, raw_response: str = "") -> None:
        self.status_code = status_code
        self.detail = detail
        self.raw_response = raw_response
        super().__init__(f"API Error (HTTP {status_code}): {detail}")


class AurenConnectionError(AurenClientError):
    """Raised when failing to connect to the Auren API server."""
    pass


class AurenContractError(AurenClientError, ValueError):
    """Raised when response payload violates API contract specifications."""
    pass


def sanitize_weights(weights_input: Union[str, Dict[str, Any]]) -> Dict[str, float]:
    """
    Parse and sanitize portfolio weights.

    Accepts:
      - dict of {ticker: weight}
      - string format e.g. "NVDA:35,MSFT:35,ETH-USD:15,SOL-USD:15"
      - string format with '=' e.g. "NVDA=35, MSFT=35"
      - JSON string format e.g. '{"NVDA": 35, "MSFT": 35}'

    Returns:
      Cleaned dict with uppercase ticker keys and positive float weights.
    """
    if weights_input is None:
        raise ValueError("Portfolio weights cannot be empty or None")

    if isinstance(weights_input, str):
        cleaned_str = weights_input.strip()
        if not cleaned_str:
            raise ValueError("Portfolio weights string cannot be empty")

        if cleaned_str.startswith("{") and cleaned_str.endswith("}"):
            try:
                parsed_json = json.loads(cleaned_str)
                if not isinstance(parsed_json, dict):
                    raise ValueError("JSON input must represent a dictionary of weights")
                weights_dict = parsed_json
            except json.JSONDecodeError as err:
                raise ValueError(f"Invalid JSON string format for weights: {err}") from err
        else:
            weights_dict = {}
            parts = [p.strip() for p in cleaned_str.replace(";", ",").split(",") if p.strip()]
            if not parts:
                raise ValueError("Portfolio weights string cannot be empty")

            for item in parts:
                if ":" in item:
                    k, v = item.split(":", 1)
                elif "=" in item:
                    k, v = item.split("=", 1)
                else:
                    raise ValueError(f"Invalid weight token '{item}': expected 'TICKER:WEIGHT' or 'TICKER=WEIGHT'")

                ticker = k.strip().upper()
                val_str = v.strip().rstrip("%")
                if not ticker:
                    raise ValueError(f"Ticker symbol cannot be empty in token '{item}'")
                try:
                    val = float(val_str)
                except ValueError as err:
                    raise ValueError(f"Invalid numeric weight '{v}' for ticker '{ticker}'") from err
                weights_dict[ticker] = val

    elif isinstance(weights_input, dict):
        if not weights_input:
            raise ValueError("Portfolio weights dictionary cannot be empty")
        weights_dict = weights_input
    else:
        raise TypeError(f"Weights must be a dict or string, got {type(weights_input).__name__}")

    sanitized: Dict[str, float] = {}
    for raw_ticker, raw_val in weights_dict.items():
        if isinstance(raw_val, bool):
            raise ValueError(f"Invalid numeric weight for ticker '{raw_ticker}': {raw_val}")
        ticker = str(raw_ticker).strip().upper()
        if not ticker:
            raise ValueError("Ticker symbol cannot be empty")
        try:
            val = float(str(raw_val).rstrip("%"))
        except (ValueError, TypeError) as err:
            raise ValueError(f"Invalid numeric weight for ticker '{ticker}': {raw_val}") from err

        if val <= 0:
            raise ValueError(f"Weight for '{ticker}' must be positive, got {val}")

        sanitized[ticker] = val

    if not sanitized:
        raise ValueError("Portfolio weights cannot be empty")

    if sum(sanitized.values()) <= 0:
        raise ValueError("Sum of portfolio weights must be greater than zero")

    return sanitized


parse_weights = sanitize_weights


def validate_contract(data: Any) -> bool:
    """
    Validate that the response dictionary satisfies the Auren Risk API contract.
    Must contain: score, level, reasons, concentration, volatility, max_drawdown,
    sector_exposure, and stress.
    """
    if not isinstance(data, dict):
        raise AurenContractError(f"API response contract violation: expected dict, got {type(data).__name__}")

    missing_fields = [f for f in REQUIRED_CONTRACT_FIELDS if f not in data]
    if missing_fields:
        raise AurenContractError(f"Missing required contract fields: {', '.join(missing_fields)}")

    if not isinstance(data["score"], (int, float)) or isinstance(data["score"], bool):
        raise AurenContractError(f"Contract violation: 'score' must be numeric, got {type(data['score']).__name__}")
    if not isinstance(data["level"], str):
        raise AurenContractError(f"Contract violation: 'level' must be string, got {type(data['level']).__name__}")
    if not isinstance(data["reasons"], list):
        raise AurenContractError(f"Contract violation: 'reasons' must be list, got {type(data['reasons']).__name__}")
    if not isinstance(data["concentration"], dict):
        raise AurenContractError(f"Contract violation: 'concentration' must be dict, got {type(data['concentration']).__name__}")
    if not isinstance(data["volatility"], (int, float)) or isinstance(data["volatility"], bool):
        raise AurenContractError(f"Contract violation: 'volatility' must be numeric, got {type(data['volatility']).__name__}")
    if not isinstance(data["max_drawdown"], (int, float)) or isinstance(data["max_drawdown"], bool):
        raise AurenContractError(f"Contract violation: 'max_drawdown' must be numeric, got {type(data['max_drawdown']).__name__}")
    if not isinstance(data["sector_exposure"], dict):
        raise AurenContractError(f"Contract violation: 'sector_exposure' must be dict, got {type(data['sector_exposure']).__name__}")
    if not isinstance(data["stress"], dict):
        raise AurenContractError(f"Contract violation: 'stress' must be dict, got {type(data['stress']).__name__}")

    return True


def format_report(data: Dict[str, Any]) -> str:
    """
    Render formatted ASCII/Unicode risk intelligence card matching AUREN specifications.
    """
    score = data.get("score", 0)
    level = str(data.get("level", "UNKNOWN")).upper()
    volatility = data.get("volatility", 0.0)
    max_dd = data.get("max_drawdown", 0.0)

    conc = data.get("concentration") or {}
    top_asset = conc.get("top_asset", "N/A")
    top_weight = conc.get("top_weight", 0.0)
    eff_assets = conc.get("effective_assets", 0.0)

    reasons = data.get("reasons") or []
    stress = data.get("stress") or {}
    disclaimer = data.get("disclaimer", "Analytics only, not investment advice.")

    # Calculate padding for scenario names (at least 30 chars for exact standard layout)
    scenario_keys = list(stress.keys())
    pad = max(30, max((len(k) for k in scenario_keys), default=30))

    score_display = f"{int(score)}" if isinstance(score, (int, float)) and int(score) == score else f"{score}"

    lines: List[str] = [
        "=" * 64,
        "AUREN RISK INTELLIGENCE REPORT".center(64),
        "=" * 64,
        f"Risk Score : {score_display} / 100",
        f"Risk Level : [{level}]",
        f"Volatility : {volatility:.1%} a year",
        f"Max DD     : {max_dd:.1%}",
        f"Top Asset  : {top_asset} ({top_weight:.1%})",
        f"Eff. Assets: {eff_assets:.1f}",
        "-" * 64,
        "FLAGGED RISK FACTORS:",
    ]

    if reasons:
        for r in reasons:
            lines.append(f"  * {r}")
    else:
        lines.append("  * None detected")

    lines.append("-" * 64)
    lines.append("STRESS SCENARIOS:")

    if stress:
        for name, impact in stress.items():
            lines.append(f"  * {name:<{pad}} : {impact:.1%}")
    else:
        lines.append("  * None evaluated")

    lines.append("-" * 64)
    if not disclaimer.startswith("Disclaimer:"):
        disclaimer = f"Disclaimer: {disclaimer}"
    lines.append(disclaimer)
    lines.append("=" * 64)

    return "\n".join(lines)


def export_json(data: Dict[str, Any], filepath: Optional[str] = None, indent: int = 2) -> str:
    """
    Export risk evaluation payload as JSON string and optionally write to disk.
    """
    json_str = json.dumps(data, indent=indent)
    if filepath:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(json_str)
    return json_str


class AurenRiskClient:
    """
    Autonomous Bounty Hunter Agent Client for the AUREN Risk Engine API (/risk).
    Pure standard library implementation with zero external dependencies.
    """

    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 10.0) -> None:
        self.base_url: str = base_url.rstrip("/")
        self.timeout: float = timeout
        self.risk_endpoint: str = f"{self.base_url}/risk"

    def sanitize_weights(self, weights: Union[str, Dict[str, Any]]) -> Dict[str, float]:
        return sanitize_weights(weights)

    parse_weights = sanitize_weights

    def validate_contract(self, data: Any) -> bool:
        return validate_contract(data)

    def assess_risk(self, weights: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Send portfolio weights to POST /risk and return validated risk metrics.
        Handles HTTP 400 and 500 errors gracefully with AurenAPIError.
        """
        cleaned_weights = self.sanitize_weights(weights)
        payload = json.dumps({"weights": cleaned_weights}).encode("utf-8")

        req = urllib.request.Request(
            self.risk_endpoint,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw_body = resp.read().decode("utf-8")
                data = json.loads(raw_body)
        except urllib.error.HTTPError as err:
            try:
                body = err.read().decode("utf-8")
                err_json = json.loads(body)
                detail = err_json.get("detail", body)
            except Exception:
                detail = str(err)
                body = ""
            raise AurenAPIError(status_code=err.code, detail=detail, raw_response=body) from err
        except urllib.error.URLError as err:
            raise AurenConnectionError(f"Failed to connect to {self.risk_endpoint}: {err.reason}") from err
        except (TimeoutError, socket.timeout) as err:
            raise AurenConnectionError(f"Request to {self.risk_endpoint} timed out after {self.timeout}s") from err
        except Exception as err:
            if isinstance(err, AurenClientError):
                raise
            raise AurenClientError(f"Unexpected error communicating with API: {err}") from err

        self.validate_contract(data)
        return data

    evaluate_risk = assess_risk
    get_risk = assess_risk

    def format_report(self, risk_data: Dict[str, Any]) -> str:
        return format_report(risk_data)

    def export_json(self, risk_data: Dict[str, Any], filepath: Optional[str] = None, indent: int = 2) -> str:
        return export_json(risk_data, filepath=filepath, indent=indent)


SAMPLE_DEMO_PORTFOLIOS: List[Dict[str, Any]] = [
    {
        "name": "High-Beta Tech & Crypto Growth",
        "weights": {"NVDA": 35, "MSFT": 35, "ETH-USD": 15, "BTC-USD": 15},
        "mock_result": {
            "score": 55,
            "level": "MEDIUM",
            "volatility": 0.284,
            "max_drawdown": -0.241,
            "concentration": {
                "top_asset": "NVDA",
                "top_weight": 0.35,
                "top3_weight": 0.85,
                "hhi": 0.29,
                "effective_assets": 3.4,
            },
            "reasons": [
                "Largest holding is 35% (over 30%)",
                "Behaves like only 3.4 assets",
            ],
            "stress": {
                "Big Tech falls 20%": -0.14,
                "Crypto drops 30%": -0.09,
            },
            "sector_exposure": {"Big Tech": 0.70, "Crypto": 0.30},
            "correlated_pairs": [["NVDA", "MSFT", 0.75]],
            "disclaimer": "Analytics only, not investment advice.",
        },
    },
    {
        "name": "Defensive Multi-Asset Balanced",
        "weights": {"AAPL": 25, "MSFT": 25, "GLD": 25, "JPM": 25},
        "mock_result": {
            "score": 20,
            "level": "LOW",
            "volatility": 0.162,
            "max_drawdown": -0.115,
            "concentration": {
                "top_asset": "AAPL",
                "top_weight": 0.25,
                "top3_weight": 0.75,
                "hhi": 0.25,
                "effective_assets": 4.0,
            },
            "reasons": [],
            "stress": {
                "Big Tech falls 20%": -0.10,
                "Broad selloff": -0.08,
            },
            "sector_exposure": {"Big Tech": 0.50, "Gold": 0.25, "Financials": 0.25},
            "correlated_pairs": [],
            "disclaimer": "Analytics only, not investment advice.",
        },
    },
    {
        "name": "Aggressive Semiconductor Focus",
        "weights": {"NVDA": 50, "AMD": 30, "TSM": 20},
        "mock_result": {
            "score": 70,
            "level": "HIGH",
            "volatility": 0.412,
            "max_drawdown": -0.385,
            "concentration": {
                "top_asset": "NVDA",
                "top_weight": 0.50,
                "top3_weight": 1.00,
                "hhi": 0.38,
                "effective_assets": 2.6,
            },
            "reasons": [
                "Largest holding is 50% (over 30%)",
                "Behaves like only 2.6 assets",
                "Volatility is 41% a year (over 30%)",
                "Worst past fall was -38% (deeper than -30%)",
            ],
            "stress": {
                "Big Tech falls 20%": -0.10,
                "Chip selloff (semis fall 25%)": -0.25,
                "NVDA falls 15%": -0.075,
            },
            "sector_exposure": {"AI & Semiconductors": 0.50, "Big Tech": 0.50},
            "correlated_pairs": [["NVDA", "AMD", 0.82]],
            "disclaimer": "Analytics only, not investment advice.",
        },
    },
]


def run_demo(client: AurenRiskClient, json_mode: bool = False, export_path: Optional[str] = None) -> int:
    """Run multi-portfolio evaluation demo."""
    all_results = []
    if not json_mode:
        print("\n" + "=" * 64)
        print("      AUREN MULTI-PORTFOLIO RISK SENTINEL DEMONSTRATION      ".center(64))
        print("=" * 64 + "\n")

    for idx, item in enumerate(SAMPLE_DEMO_PORTFOLIOS, 1):
        name = item["name"]
        weights = item["weights"]
        weights_str = ", ".join(f"{k}:{v}%" for k, v in weights.items())

        if not json_mode:
            print(f"Portfolio {idx}/{len(SAMPLE_DEMO_PORTFOLIOS)}: {name}")
            print(f"Allocation: {weights_str}")

        try:
            res = client.assess_risk(weights)
            mode_tag = "LIVE API"
        except (AurenClientError, urllib.error.URLError):
            res = item["mock_result"]
            mode_tag = "DEMO SIMULATION"

        all_results.append({"portfolio": name, "weights": weights, "risk_data": res})

        if not json_mode:
            print(f"Engine Mode: [{mode_tag}]")
            print(client.format_report(res))
            print()

    if json_mode:
        output_data = all_results if len(all_results) > 1 else all_results[0]["risk_data"]
        json_out = json.dumps(output_data, indent=2)
        print(json_out)

    if export_path:
        export_json({"portfolios": all_results}, filepath=export_path)
        if not json_mode:
            print(f"[+] Demo results exported to: {export_path}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AUREN Risk Sentinel & Autonomous Agent Multi-Asset Risk Client"
    )
    parser.add_argument(
        "--weights",
        type=str,
        help='Portfolio weights (e.g. "NVDA:35,MSFT:35,ETH-USD:15,BTC-USD:15")',
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run multi-portfolio risk sentinel demo",
    )
    parser.add_argument(
        "--url",
        "--api-url",
        dest="api_url",
        type=str,
        default="http://localhost:8000",
        help="Base URL of AUREN Risk API (default: http://localhost:8000)",
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
        help="Output raw JSON response",
    )
    parser.add_argument(
        "--export",
        "--output",
        dest="export_path",
        type=str,
        help="Save evaluation JSON to file",
    )

    args = parser.parse_args()

    client = AurenRiskClient(base_url=args.api_url, timeout=args.timeout)

    if args.demo:
        return run_demo(client, json_mode=args.json, export_path=args.export_path)

    if args.weights:
        try:
            risk_data = client.assess_risk(args.weights)
        except AurenAPIError as err:
            print(f"[!] API Error (HTTP {err.status_code}): {err.detail}", file=sys.stderr)
            return 1
        except AurenConnectionError as err:
            print(f"[!] Connection Error: {err}", file=sys.stderr)
            print("    Please ensure the AUREN Risk API server is running.", file=sys.stderr)
            return 1
        except ValueError as err:
            print(f"[!] Input Error: {err}", file=sys.stderr)
            return 1
        except Exception as err:
            print(f"[!] Unexpected Error: {err}", file=sys.stderr)
            return 1

        if args.export_path:
            client.export_json(risk_data, filepath=args.export_path)
            if not args.json:
                print(f"[+] Risk intelligence exported to: {args.export_path}")

        if args.json:
            print(client.export_json(risk_data))
        else:
            print(client.format_report(risk_data))
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
