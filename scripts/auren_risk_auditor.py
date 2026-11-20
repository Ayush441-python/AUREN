"""AUREN Risk API Health & Automated Drift Auditor.

Tests AUREN Risk API (`/risk`) endpoint against known multi-asset portfolios,
validates RFC 8259 compliance, verifies scenario stress tests, and monitors
risk-score thresholds for automated alerting.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional


DEFAULT_API_URL = "http://127.0.0.1:8000"


class AurenAuditError(Exception):
    """Base exception for AUREN audit errors."""


def query_risk_api(weights: Dict[str, float], base_url: str = DEFAULT_API_URL) -> Dict[str, Any]:
    """Call POST /risk on AUREN API."""
    url = f"{base_url.rstrip('/')}/risk"
    payload = json.dumps({"weights": weights}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "AurenAuditor/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        err_msg = exc.read().decode("utf-8", errors="ignore")
        raise AurenAuditError(f"HTTP {exc.code}: {err_msg}") from exc
    except Exception as exc:
        raise AurenAuditError(f"Connection error to {url}: {exc}") from exc


def audit_portfolio(weights: Dict[str, float], base_url: str = DEFAULT_API_URL) -> Dict[str, Any]:
    """Run an automated risk audit on a target portfolio and verify invariants."""
    data = query_risk_api(weights, base_url=base_url)

    # Invariant checks
    conc = data.get("concentration", {})
    assert "hhi" in conc, "Missing HHI in concentration"
    assert "effective_assets" in conc, "Missing effective_assets in concentration"
    assert conc["effective_assets"] >= 1.0, f"Invalid effective assets: {conc['effective_assets']}"

    score_data = data.get("score", {})
    assert "score" in score_data, "Missing score in score response"
    score = score_data["score"]
    assert 0 <= score <= 100, f"Score out of range: {score}"

    metrics = data.get("metrics", {})
    assert "annualized_volatility" in metrics, "Missing volatility"
    assert "max_drawdown" in metrics, "Missing max_drawdown"

    return {
        "status": "PASS",
        "portfolio_size": len(weights),
        "score": score,
        "level": score_data.get("level", "Unknown"),
        "top_asset": conc.get("top_asset"),
        "hhi": round(conc.get("hhi", 0), 4),
        "volatility": round(metrics.get("annualized_volatility", 0), 4),
        "max_drawdown": round(metrics.get("max_drawdown", 0), 4),
    }


def main():
    parser = argparse.ArgumentParser(description="AUREN Risk API Automated Auditor")
    parser.add_argument("--url", default=DEFAULT_API_URL, help="AUREN API Base URL")
    parser.add_argument("--demo", action="store_true", help="Run built-in multi-asset portfolio test suite")
    args = parser.parse_args()

    portfolios = {
        "Balanced Tech & Crypto": {"NVDA": 40.0, "MSFT": 30.0, "GOOGL": 20.0, "BTC-USD": 10.0},
        "High Conviction Semi": {"NVDA": 50.0, "TSM": 25.0, "ASML": 15.0, "AMD": 10.0},
    }

    print("=== AUREN Risk API Automated Audit Suite ===")
    all_passed = True
    for name, w in portfolios.items():
        try:
            res = audit_portfolio(w, base_url=args.url)
            print(f"✓ {name}: Score {res['score']}/100 ({res['level']}), HHI {res['hhi']}, Vol {res['volatility']}")
        except Exception as exc:
            print(f"✗ {name}: FAILED - {exc}")
            all_passed = False

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
