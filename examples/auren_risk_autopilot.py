#!/usr/bin/env python3
"""AUREN Risk Autopilot — Standalone external client & de-escalation solver for the AUREN Risk API.

Zero external dependencies (Python 3.10+ stdlib). Calls live production /risk and /liquidity
endpoints, audits rule violations, synthesizes a minimum-turnover de-risked allocation across
defensive uncorrelated sleeves, and verifies the post-rebalance portfolio via a second /risk call.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

DEFAULT_API = "https://auren-api-8yrq.onrender.com"

DEFENSIVE_BALLAST = [
    ("GLD", "Gold"),
    ("TLT", "Bonds & Fixed Income"),
    ("SPY", "Broad Market ETFs"),
    ("JPM", "Financials"),
    ("COST", "Consumer & Retail"),
    ("XOM", "Industrial & Energy"),
]

DEFAULT_PORTFOLIO = {
    "NVDA": 40.0,
    "MSFT": 30.0,
    "GOOGL": 20.0,
    "ETH-USD": 10.0,
}


def post_json(base_url: str, path: str, payload: dict, timeout: int = 35) -> dict:
    url = base_url.rstrip("/") + path
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "auren-risk-autopilot/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        raise RuntimeError(f"HTTP {e.code} calling {url}: {detail}") from e


def synthesize_deescalated_weights(
    normalized_weights: dict[str, float],
    max_single_weight: float = 0.20,
) -> dict[str, float]:
    """Build a diversified minimum-turnover rebalance that caps single-name weight,
    lifts effective assets above 4, and diversifies tech/crypto concentration via uncorrelated ballast."""
    capped = {k: min(float(v), max_single_weight) for k, v in normalized_weights.items()}
    # Scale existing high-beta sleeve so non-correlated defensive assets receive >= 45%
    total_capped = sum(capped.values())
    risky_budget = min(0.50, total_capped)
    scale = risky_budget / total_capped if total_capped > 0 else 0.0
    proposed = {k: round(v * scale, 4) for k, v in capped.items()}

    missing_ballast = [t for t, _ in DEFENSIVE_BALLAST if t not in proposed]
    rem = round(1.0 - sum(proposed.values()), 4)
    if missing_ballast and rem > 0:
        each = round(rem / len(missing_ballast), 4)
        for i, ticker in enumerate(missing_ballast):
            proposed[ticker] = each if i < len(missing_ballast) - 1 else round(1.0 - sum(proposed.values()), 4)

    # Ensure positive normalization sums cleanly to 1.0
    total = sum(proposed.values())
    return {k: round(v / total, 4) for k, v in proposed.items() if v > 0}


def audit_and_rebalance(
    api_base: str,
    weights: dict[str, float],
    portfolio_value: float = 100_000.0,
) -> dict:
    before_risk = post_json(api_base, "/risk", {"weights": weights, "period": "2y"})
    before_liq = post_json(
        api_base,
        "/liquidity",
        {"portfolio_value": portfolio_value, "weights": weights, "adv_participation": 0.10},
    )

    proposed_weights = synthesize_deescalated_weights(before_risk["normalized_weights"])
    after_risk = post_json(api_base, "/risk", {"weights": proposed_weights, "period": "2y"})
    after_liq = post_json(
        api_base,
        "/liquidity",
        {"portfolio_value": portfolio_value, "weights": proposed_weights, "adv_participation": 0.10},
    )

    # Calculate 1-way portfolio turnover
    all_tickers = set(before_risk["normalized_weights"]) | set(after_risk["normalized_weights"])
    turnover = 0.5 * sum(
        abs(after_risk["normalized_weights"].get(t, 0.0) - before_risk["normalized_weights"].get(t, 0.0))
        for t in all_tickers
    )

    return {
        "api_base": api_base,
        "portfolio_value_usd": portfolio_value,
        "before": {
            "score": before_risk["score"],
            "level": before_risk["level"],
            "volatility": before_risk["volatility"],
            "max_drawdown": before_risk["max_drawdown"],
            "effective_assets": before_risk["concentration"]["effective_assets"],
            "top_weight": before_risk["concentration"]["top_weight"],
            "max_days_to_exit": before_liq["max_days_to_exit"],
            "reasons": before_risk["reasons"],
            "weights": before_risk["normalized_weights"],
        },
        "after": {
            "score": after_risk["score"],
            "level": after_risk["level"],
            "volatility": after_risk["volatility"],
            "max_drawdown": after_risk["max_drawdown"],
            "effective_assets": after_risk["concentration"]["effective_assets"],
            "top_weight": after_risk["concentration"]["top_weight"],
            "max_days_to_exit": after_liq["max_days_to_exit"],
            "reasons": after_risk["reasons"],
            "weights": after_risk["normalized_weights"],
        },
        "delta": {
            "score_reduction": before_risk["score"] - after_risk["score"],
            "volatility_reduction": round(before_risk["volatility"] - after_risk["volatility"], 4),
            "one_way_turnover": round(turnover, 4),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="AUREN Risk Autopilot external API integration agent")
    ap.add_argument("--api", default=DEFAULT_API, help=f"AUREN API base URL (default: {DEFAULT_API})")
    ap.add_argument(
        "--weights",
        default=json.dumps(DEFAULT_PORTFOLIO),
        help="JSON dict of ticker -> weight",
    )
    ap.add_argument("--value", type=float, default=100_000.0, help="Portfolio USD value for /liquidity")
    ap.add_argument("--json-out", help="Optional path to save full JSON audit receipt")
    args = ap.parse_args()

    weights = json.loads(args.weights)
    report = audit_and_rebalance(args.api, weights, portfolio_value=args.value)

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
            fh.write("\n")

    b, a, d = report["before"], report["after"], report["delta"]
    print(f"=== AUREN Risk Autopilot ({report['api_base']}) ===")
    print(f"Before: Score={b['score']} ({b['level']}) | Vol={b['volatility']*100:.1f}% | MDD={b['max_drawdown']*100:.1f}% | EffAssets={b['effective_assets']:.2f} | MaxExit={b['max_days_to_exit']:.3f}d")
    print(f"  Triggered Rules: {b['reasons']}")
    print(f"After : Score={a['score']} ({a['level']}) | Vol={a['volatility']*100:.1f}% | MDD={a['max_drawdown']*100:.1f}% | EffAssets={a['effective_assets']:.2f} | MaxExit={a['max_days_to_exit']:.3f}d")
    print(f"  Triggered Rules: {a['reasons']}")
    print(f"Delta : -{d['score_reduction']} risk pts | -{d['volatility_reduction']*100:.1f}% vol | {d['one_way_turnover']*100:.1f}% one-way turnover")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
