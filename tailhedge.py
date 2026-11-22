#!/usr/bin/env python3
"""
AUREN TailHedge: Autonomous Portfolio Tail-Risk Mitigation & Hedging Agent
Built for AUREN /risk API Integration Bounty (#198).
Standard library only (Python 3.10+).
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
from typing import Dict, Any, Tuple, List, Optional

DEFENSIVE_CANDIDATES = ["GLD", "PEP", "XEL", "JPM", "XOM"]


class TailHedge:
    def __init__(self, api_url: str = "https://auren-api-8yrq.onrender.com"):
        self.api_url = api_url.rstrip("/")

    @staticmethod
    def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
        """Normalize raw portfolio weights to sum exactly to 1.0."""
        total = sum(weights.values())
        if total <= 0:
            raise ValueError("Portfolio weights sum must be greater than zero.")
        return {k: round(v / total, 6) for k, v in weights.items()}

    @staticmethod
    def calculate_hedged_weights(
        weights: Dict[str, float],
        hedge_asset: str = "GLD",
        hedge_ratio: float = 0.20
    ) -> Dict[str, float]:
        """
        Synthesize hedged allocation: allocates hedge_ratio to hedge_asset
        and proportionally dilutes existing risk positions.
        """
        if not (0.0 < hedge_ratio < 1.0):
            raise ValueError(f"Hedge ratio must be between 0 and 1, got {hedge_ratio}")

        normalized = TailHedge.normalize_weights(weights)
        scale = 1.0 - hedge_ratio
        hedged = {k: round(v * scale, 6) for k, v in normalized.items()}

        if hedge_asset in hedged:
            hedged[hedge_asset] = round(hedged[hedge_asset] + hedge_ratio, 6)
        else:
            hedged[hedge_asset] = round(hedge_ratio, 6)

        return TailHedge.normalize_weights(hedged)

    def query_risk(self, weights: Dict[str, float], timeout: int = 20) -> Dict[str, Any]:
        """Query AUREN POST /risk endpoint with portfolio weights."""
        url = f"{self.api_url}/risk"
        req_body = json.dumps({"weights": weights}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=req_body,
            headers={"Content-Type": "application/json", "User-Agent": "AUREN-TailHedge/1.0"}
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"API HTTP {e.code}: {err_msg}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Network error contacting AUREN API: {e.reason}")

    @staticmethod
    def generate_rebalancing_orders(
        initial_weights: Dict[str, float],
        hedged_weights: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Generate precise BUY / SELL delta rebalancing orders."""
        all_tickers = sorted(set(initial_weights.keys()) | set(hedged_weights.keys()))
        orders = []

        for t in all_tickers:
            w_init = initial_weights.get(t, 0.0)
            w_hedge = hedged_weights.get(t, 0.0)
            delta = round(w_hedge - w_init, 6)

            if abs(delta) >= 0.0001:
                action = "BUY" if delta > 0 else "SELL"
                orders.append({
                    "ticker": t,
                    "action": action,
                    "initial_weight": w_init,
                    "hedged_weight": w_hedge,
                    "delta_pct": delta
                })

        return orders

    @staticmethod
    def compare_metrics(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
        """Compute relative deltas between unhedged and hedged risk profiles."""
        score_before = before.get("score", 0)
        score_after = after.get("score", 0)

        vol_before = before.get("volatility", 0.0)
        vol_after = after.get("volatility", 0.0)
        vol_change_pct = ((vol_after - vol_before) / vol_before * 100.0) if vol_before > 0 else 0.0

        mdd_before = before.get("max_drawdown", 0.0)
        mdd_after = after.get("max_drawdown", 0.0)
        mdd_impr_pct = ((abs(mdd_before) - abs(mdd_after)) / abs(mdd_before) * 100.0) if mdd_before != 0 else 0.0

        eff_before = before.get("effective_assets", 0.0)
        eff_after = after.get("effective_assets", 0.0)

        worst_stress_before = None
        worst_stress_after = None
        if "stress_tests" in before and isinstance(before["stress_tests"], list) and before["stress_tests"]:
            worst_stress_before = min(before["stress_tests"], key=lambda s: s.get("portfolio_impact", 0.0))
        if "stress_tests" in after and isinstance(after["stress_tests"], list) and after["stress_tests"]:
            worst_stress_after = min(after["stress_tests"], key=lambda s: s.get("portfolio_impact", 0.0))

        return {
            "score_delta": score_after - score_before,
            "score_before": score_before,
            "score_after": score_after,
            "volatility_before": vol_before,
            "volatility_after": vol_after,
            "volatility_change_pct": round(vol_change_pct, 2),
            "max_drawdown_before": mdd_before,
            "max_drawdown_after": mdd_after,
            "mdd_improvement_pct": round(mdd_impr_pct, 2),
            "effective_assets_before": eff_before,
            "effective_assets_after": eff_after,
            "effective_assets_delta": round(eff_after - eff_before, 2),
            "worst_stress_before": worst_stress_before,
            "worst_stress_after": worst_stress_after,
            "is_effective": (score_after <= score_before) and (vol_after <= vol_before)
        }

    def auto_optimize(
        self,
        weights: Dict[str, float],
        candidates: Optional[List[str]] = None,
        hedge_ratio: float = 0.20
    ) -> Tuple[str, Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """Scan candidate defense assets to identify optimal tail-risk mitigant."""
        if candidates is None:
            candidates = DEFENSIVE_CANDIDATES

        initial_risk = self.query_risk(weights)
        best_asset = candidates[0]
        best_comparison = None
        best_hedged_risk = None
        best_hedged_weights = None
        min_volatility = float("inf")

        for asset in candidates:
            h_weights = self.calculate_hedged_weights(weights, hedge_asset=asset, hedge_ratio=hedge_ratio)
            h_risk = self.query_risk(h_weights)
            comparison = self.compare_metrics(initial_risk, h_risk)

            vol = h_risk.get("volatility", float("inf"))
            if vol < min_volatility:
                min_volatility = vol
                best_asset = asset
                best_comparison = comparison
                best_hedged_risk = h_risk
                best_hedged_weights = h_weights

        return best_asset, best_hedged_weights, best_hedged_risk, best_comparison


def main():
    parser = argparse.ArgumentParser(
        description="AUREN TailHedge: Autonomous Tail-Risk Mitigation & Hedging Agent"
    )
    parser.add_argument("--api-url", default="https://auren-api-8yrq.onrender.com", help="AUREN backend base URL")
    parser.add_argument("--weights", help="Raw JSON string of portfolio weights")
    parser.add_argument("--weights-file", help="Path to JSON file containing portfolio weights")
    parser.add_argument("--hedge-asset", default="GLD", help="Defensive hedge asset symbol (default: GLD)")
    parser.add_argument("--hedge-ratio", type=float, default=0.20, help="Target allocation for hedge asset (0.01-0.99)")
    parser.add_argument("--auto-optimize", action="store_true", help="Automatically search optimal hedge asset")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON result")

    args = parser.parse_args()

    # Load weights
    if args.weights:
        raw_weights = json.loads(args.weights)
    elif args.weights_file:
        with open(args.weights_file, "r", encoding="utf-8") as f:
            raw_weights = json.load(f)
    else:
        # Default high-beta tech/crypto sample portfolio
        raw_weights = {"NVDA": 0.40, "BTC-USD": 0.30, "ETH-USD": 0.30}

    agent = TailHedge(api_url=args.api_url)

    if args.auto_optimize:
        best_asset, hedged_weights, after_risk, comparison = agent.auto_optimize(
            raw_weights, hedge_ratio=args.hedge_ratio
        )
        before_risk = agent.query_risk(raw_weights)
        target_asset = best_asset
    else:
        target_asset = args.hedge_asset
        hedged_weights = agent.calculate_hedged_weights(raw_weights, hedge_asset=target_asset, hedge_ratio=args.hedge_ratio)
        before_risk = agent.query_risk(raw_weights)
        after_risk = agent.query_risk(hedged_weights)
        comparison = agent.compare_metrics(before_risk, after_risk)

    orders = agent.generate_rebalancing_orders(raw_weights, hedged_weights)

    if args.json:
        out = {
            "initial_weights": raw_weights,
            "hedged_weights": hedged_weights,
            "hedge_asset": target_asset,
            "hedge_ratio": args.hedge_ratio,
            "comparison": comparison,
            "rebalancing_orders": orders
        }
        print(json.dumps(out, indent=2))
        return 0

    print("=" * 64)
    print("          AUREN TailHedge — Hedging & Risk Mitigation Agent      ")
    print("=" * 64)
    print(f"Target Hedge Asset: {target_asset} | Allocation: {args.hedge_ratio * 100:.1f}%")
    print("-" * 64)
    print("RISK METRICS COMPARISON (Before vs After Hedge):")
    print(f"  * Risk Score:        {comparison['score_before']:<4} -->  {comparison['score_after']:<4} [Delta: {comparison['score_delta']:+d} pts]")
    print(f"  * Volatility:       {comparison['volatility_before']*100:.2f}%  --> {comparison['volatility_after']*100:.2f}%  [Change: {comparison['volatility_change_pct']:+.2f}%]")
    print(f"  * Max Drawdown:     {comparison['max_drawdown_before']*100:.2f}%  --> {comparison['max_drawdown_after']*100:.2f}%  [Improvement: {comparison['mdd_improvement_pct']:+.2f}%]")
    print(f"  * Effective Assets:  {comparison['effective_assets_before']:.2f}  -->  {comparison['effective_assets_after']:.2f}  [Delta: {comparison['effective_assets_delta']:+.2f}]")
    if comparison["worst_stress_after"]:
        ws = comparison["worst_stress_after"]
        print(f"  * Worst Stress:     {ws.get('portfolio_impact', 0)*100:.2f}%  ({ws.get('scenario_name', 'Scenario')})")
    print("-" * 64)
    print("PORTFOLIO ALLOCATION & REBALANCING ORDERS:")
    for o in orders:
        t = o["ticker"]
        init_p = o["initial_weight"] * 100
        hedge_p = o["hedged_weight"] * 100
        delta_p = o["delta_pct"] * 100
        action = o["action"]
        print(f"  {t:<10}  Initial: {init_p:5.1f}%  ->  Hedged: {hedge_p:5.1f}%  |  {action} {delta_p:+6.2f}%")
    print("-" * 64)
    status_str = "HEDGE EFFECTIVE: Risk successfully mitigated" if comparison["is_effective"] else "HEDGE ADVISORY: Review portfolio constraints"
    print(f"STATUS: {status_str}")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    sys.exit(main())
