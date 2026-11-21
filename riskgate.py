#!/usr/bin/env python3
"""riskgate — ALLOW/BLOCK pre-trade policy gate over the AUREN /risk API.

External-agent demo for AUREN API Integration tier ($25 USDC):
https://github.com/Ayush441-python/AUREN/issues/166

Standard library only, no API key, Python 3.10+.

Usage:
    python3 riskgate.py --weights '{"NVDA":40,"MSFT":30,"GOOGL":20,"ETH-USD":10}' \
                        --portfolio-value 100000
    python3 riskgate.py --weights '{"JPM":20,"XOM":20,"GLD":20,"PEP":20,"XEL":20}' \
                        --json

Exit status is 0 for ALLOW and 1 for BLOCK, so it drops into a shell guard.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_API_BASE = "https://auren-api-8yrq.onrender.com"

# Policy defaults. Each rule reports the limit that was breached.
DEFAULT_POLICY: Dict[str, float] = {
    "max_score": 64.0,            # refuse an AUREN score of 65+ (the High band)
    "max_top_weight": 0.40,       # largest single holding
    "min_effective_assets": 3.0,  # 1/HHI floor
    "max_sector_share": 0.60,     # largest broad-group share
    "max_days_to_exit": 20.0,     # liquidity cap, only with a position size
}

POLICY_BOUNDS: Dict[str, Tuple[float, float]] = {
    "max_score": (0.0, 100.0),
    "max_top_weight": (0.0, 1.0),
    "min_effective_assets": (0.0, 1000.0),
    "max_sector_share": (0.0, 1.0),
    "max_days_to_exit": (0.0, 1e6),
}

REASON_TEXT = {
    "score": "risk score is at or above the High band",
    "top_weight": "too much of the portfolio is one holding",
    "effective_assets": "portfolio behaves like too few independent assets",
    "sector_share": "too much of the portfolio is one correlated bet",
    "days_to_exit": "portfolio cannot be exited within the liquidity limit",
}


class PolicyError(ValueError):
    pass


def load_policy(overrides: Optional[Dict[str, Any]]) -> Dict[str, float]:
    """Merge CLI overrides into DEFAULT_POLICY; unknown keys raise rather than
    silently disabling a limit."""
    policy = dict(DEFAULT_POLICY)
    if overrides:
        unknown = sorted(set(overrides) - set(DEFAULT_POLICY))
        if unknown:
            raise PolicyError(
                f"unknown policy keys {unknown}; valid keys: {sorted(DEFAULT_POLICY)}"
            )
        policy.update(overrides)
    for key, value in policy.items():
        try:
            policy[key] = float(value)
        except (TypeError, ValueError):
            raise PolicyError(f"policy key {key!r} must be numeric, got {value!r}")
        lo, hi = POLICY_BOUNDS[key]
        if not (lo <= policy[key] <= hi):
            raise PolicyError(
                f"policy key {key!r}={policy[key]} outside allowed range [{lo}, {hi}]"
            )
    return policy


def post_json(url: str, payload: Dict[str, Any], timeout: float = 60.0) -> Dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"{url} returned HTTP {e.code}: {detail}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"{url} unreachable: {e.reason}") from e


def max_sector_share(risk_doc: Dict[str, Any]) -> float:
    exposure = risk_doc.get("sector_exposure") or {}
    return float(max(exposure.values(), default=0.0))


def evaluate(
    risk_doc: Dict[str, Any],
    policy: Dict[str, float],
    liquidity_doc: Optional[Dict[str, Any]] = None,
) -> Tuple[str, List[Dict[str, Any]]]:
    """Apply every policy rule and report ALL breaches, not just the first.

    Returns (verdict, breaches) where each breach is
    {"rule", "value", "limit", "detail"}.
    """
    breaches: List[Dict[str, Any]] = []

    def breach(rule: str, value: Any, limit: float) -> None:
        breaches.append(
            {
                "rule": rule,
                "value": value,
                "limit": limit,
                "detail": f"{rule}={value} (limit {limit})",
            }
        )

    score = risk_doc.get("score")
    if score is None:
        raise RuntimeError("/risk response missing 'score'")
    if float(score) > policy["max_score"]:
        breach("score", score, policy["max_score"])

    conc = risk_doc.get("concentration") or {}
    top_weight = conc.get("top_weight")
    if top_weight is not None and float(top_weight) > policy["max_top_weight"]:
        breach("top_weight", top_weight, policy["max_top_weight"])

    eff = conc.get("effective_assets")
    if eff is not None and float(eff) < policy["min_effective_assets"]:
        breach("effective_assets", eff, policy["min_effective_assets"])

    sector = max_sector_share(risk_doc)
    if sector > policy["max_sector_share"]:
        breach("sector_share", round(sector, 4), policy["max_sector_share"])

    if liquidity_doc is not None:
        days = liquidity_doc.get("max_days_to_exit")
        if days is not None and float(days) > policy["max_days_to_exit"]:
            breach("days_to_exit", days, policy["max_days_to_exit"])

    return ("BLOCK" if breaches else "ALLOW", breaches)


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def render_text(verdict: str, breaches: List[Dict[str, Any]]) -> str:
    if verdict == "ALLOW":
        return "ALLOW: every policy limit is satisfied"
    reasons = []
    for b in breaches:
        reasons.append(REASON_TEXT.get(b["rule"], b["rule"]))
    head = f"BLOCK: {'; '.join(reasons)}"
    lines = [head]
    for b in breaches:
        lines.append(f"  - {b['rule']}={_fmt(b['value'])} (limit {_fmt(b['limit'])})")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="riskgate",
        description="ALLOW/BLOCK pre-trade policy gate over the AUREN /risk API.",
    )
    p.add_argument(
        "--weights",
        required=True,
        help='JSON object of ticker -> weight, e.g. \'{"NVDA":40,"MSFT":30}\'',
    )
    p.add_argument(
        "--portfolio-value",
        type=float,
        default=None,
        help="Portfolio value in USD; enables the /liquidity days_to_exit rule",
    )
    p.add_argument(
        "--period",
        default="2y",
        help="Historical lookback period for /risk (default: 2y)",
    )
    p.add_argument(
        "--api-base",
        default=DEFAULT_API_BASE,
        help=f"AUREN API base URL (default: {DEFAULT_API_BASE})",
    )
    p.add_argument(
        "--policy",
        default=None,
        help='JSON object overriding policy limits, e.g. \'{"max_score": 50}\'',
    )
    p.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Emit the full record (raw /risk doc, /liquidity result, verdict) as JSON",
    )
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        weights = json.loads(args.weights)
        if not isinstance(weights, dict) or not weights:
            raise ValueError("--weights must be a non-empty JSON object")
        weights = {str(k): float(v) for k, v in weights.items()}
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        print(f"error: invalid --weights: {e}", file=sys.stderr)
        return 2

    try:
        policy_overrides = json.loads(args.policy) if args.policy else None
        if policy_overrides is not None and not isinstance(policy_overrides, dict):
            raise PolicyError("--policy must be a JSON object")
        policy = load_policy(policy_overrides)
    except (json.JSONDecodeError, PolicyError) as e:
        print(f"error: invalid --policy: {e}", file=sys.stderr)
        return 2

    api_base = args.api_base.rstrip("/")
    risk_doc = post_json(f"{api_base}/risk", {"weights": weights, "period": args.period})

    liquidity_doc = None
    if args.portfolio_value is not None:
        if args.portfolio_value <= 0:
            print("error: --portfolio-value must be > 0", file=sys.stderr)
            return 2
        liquidity_doc = post_json(
            f"{api_base}/liquidity",
            {
                "portfolio_value": args.portfolio_value,
                "weights": weights,
                "period": "1y",
            },
        )

    verdict, breaches = evaluate(risk_doc, policy, liquidity_doc)

    if args.as_json:
        print(
            json.dumps(
                {
                    "verdict": verdict,
                    "policy": policy,
                    "breaches": breaches,
                    "risk": risk_doc,
                    "liquidity": liquidity_doc,
                },
                indent=2,
            )
        )
    else:
        print(render_text(verdict, breaches))

    return 0 if verdict == "ALLOW" else 1


if __name__ == "__main__":
    sys.exit(main())
