"""
AUREN External Risk Analytics Agent & Dashboard Client
=====================================================
A production-grade Python client agent and CLI dashboard that integrates with the
AUREN Risk API (/risk) to extract, analyze, and format real-time portfolio risk telemetry.

Author / Contributor: Mhamed Askoure (@zongsm-cmyk)
Settlement Rail: USDC on Base Mainnet (0xC10373008eFb38192C87C375ac63aB12E27C684C)
"""

import argparse
import json
import sys
import urllib.request
import urllib.error


def render_gauge(score: int, width: int = 30) -> str:
    """Renders an ASCII score bar from 0 to 100."""
    filled = int((score / 100.0) * width)
    empty = width - filled
    bar = "█" * filled + "░" * empty
    if score < 35:
        tag = "[LOW RISK]"
    elif score < 65:
        tag = "[MEDIUM RISK]"
    else:
        tag = "[HIGH RISK]"
    return f"[{bar}] {score}/100 {tag}"


def call_auren_risk_api(endpoint: str, weights: dict[str, float]) -> dict:
    """Calls the AUREN /risk endpoint with portfolio weights."""
    url = endpoint.rstrip("/") + "/risk"
    payload = json.dumps({"weights": weights}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "AurenAgentClient/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"AUREN API Error ({e.code}): {err_body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Connection to AUREN API failed: {e.reason}") from e


def display_risk_dashboard(weights: dict[str, float], report: dict):
    """Prints a structured institutional-grade terminal risk report."""
    print("\n" + "=" * 65)
    print("       A U R E N   P O R T F O L I O   R I S K   R E P O R T")
    print("=" * 65)

    # 1. Input Allocations
    print("\n[1] ALLOCATION WEIGHTS:")
    total_w = sum(weights.values())
    for ticker, val in weights.items():
        norm_pct = (val / total_w) * 100.0
        bar = "■" * int(norm_pct / 4)
        print(f"  • {ticker:<8} : {norm_pct:>5.1f}%  {bar}")

    # 2. Risk Score & Level
    score = report.get("score", 0)
    level = report.get("level", "Unknown")
    print(f"\n[2] COMPOSITE RISK SCORE: {score}/100 ({level})")
    print(f"  {render_gauge(score)}")

    # 3. Triggered Rules
    reasons = report.get("reasons", [])
    if reasons:
        print("\n[3] RISK ALERTS & TRIGGERED RULES:")
        for r in reasons:
            print(f"  ⚠️  {r}")
    else:
        print("\n[3] RISK ALERTS: None (Safe Profile)")

    # 4. Core Statistical Metrics
    conc = report.get("concentration", {})
    vol = report.get("volatility", 0.0)
    mdd = report.get("max_drawdown", 0.0)
    print("\n[4] KEY RISK METRICS:")
    print(f"  • Annualized Volatility:     {vol:>6.1%}")
    print(f"  • Max Peak-to-Trough Drop:   {mdd:>6.1%}")
    print(f"  • Effective Holding Units:   {conc.get('effective_assets', 0):>6.2f} assets")
    print(f"  • Top Asset Concentration:   {conc.get('top_asset', 'N/A')} ({conc.get('top_weight', 0):.1%})")
    print(f"  • Herfindahl Index (HHI):    {conc.get('hhi', 0):>6.3f}")

    # 5. Stress Testing Scenarios
    stress_results = report.get("stress", {})
    if stress_results:
        print("\n[5] MARKET STRESS SIMULATIONS:")
        for name, impact in stress_results.items():
            impact_pct = impact * 100.0
            print(f"  • {name:<32} : {impact_pct:>+6.2f}%")

    # 6. Highly Correlated Pairs
    corr_pairs = report.get("correlated_pairs", [])
    if corr_pairs:
        print("\n[6] HIGH-CORRELATION PAIRS (r > 0.70):")
        for a, b, r in corr_pairs:
            print(f"  🔗 {a} <--> {b} (correlation: {r:.2f})")

    # 7. Sector Exposure
    exposure = report.get("sector_exposure", {})
    if exposure:
        print("\n[7] SECTOR / GROUP EXPOSURE:")
        for sector, exp_val in exposure.items():
            print(f"  • {sector:<28} : {exp_val:>5.1%}")

    print("\n" + "=" * 65)
    print("Disclaimer: Analytics only, not financial investment advice.")
    print("=" * 65 + "\n")


def main():
    parser = argparse.ArgumentParser(description="AUREN External Risk Client Agent")
    parser.add_argument(
        "--endpoint",
        default="http://localhost:8000",
        help="AUREN Risk API base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--portfolio",
        default='{"NVDA": 40, "MSFT": 30, "GOOGL": 20, "ETH-USD": 10}',
        help="JSON string of portfolio weights",
    )
    args = parser.parse_args()

    try:
        weights = json.loads(args.portfolio)
    except json.JSONDecodeError as e:
        print(f"Error parsing portfolio JSON: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Connecting to AUREN Risk API at {args.endpoint}...")
    try:
        report = call_auren_risk_api(args.endpoint, weights)
        display_risk_dashboard(weights, report)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
