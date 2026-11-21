"""Tests for riskgate — the AUREN /risk pre-trade policy gate.

Ten tests pin the pure decision function and policy validation offline.
One live test calls the real AUREN API and SKIPS (rather than fails) when
the API is unreachable, so CI stays honest about what it actually reached.

Run: python3 -m pytest test_riskgate.py  (or: python3 test_riskgate.py)
"""

import pytest

import riskgate
from riskgate import (
    DEFAULT_POLICY,
    PolicyError,
    evaluate,
    load_policy,
    main,
    max_sector_share,
    post_json,
    render_text,
)


# --- fixtures: minimal /risk and /liquidity documents ---

def risk_doc(score=10, top_weight=0.2, effective_assets=8.0, sector_share=0.5):
    return {
        "score": score,
        "level": "Low" if score < 40 else "High",
        "concentration": {
            "top_asset": "AAA",
            "top_weight": top_weight,
            "top3_weight": 0.5,
            "hhi": 0.125,
            "effective_assets": effective_assets,
        },
        "volatility": 0.1,
        "max_drawdown": -0.05,
        "sector_exposure": {"Tech": sector_share, "Energy": 1.0 - sector_share},
        "correlated_pairs": [],
    }


def liq_doc(days=5.0):
    return {"portfolio_value": 100000.0, "max_days_to_exit": days, "assets": []}


# --- offline tests ---

def test_clean_book_allows():
    verdict, breaches = evaluate(risk_doc(), dict(DEFAULT_POLICY), liq_doc())
    assert verdict == "ALLOW"
    assert breaches == []


def test_score_at_limit_allows_but_above_blocks():
    # Boundary: limit 64 refuses 65+ (High band), exactly 64 is allowed.
    assert evaluate(risk_doc(score=64), dict(DEFAULT_POLICY))[0] == "ALLOW"
    verdict, breaches = evaluate(risk_doc(score=65), dict(DEFAULT_POLICY))
    assert verdict == "BLOCK"
    assert breaches[0]["rule"] == "score"
    assert breaches[0]["value"] == 65


def test_top_weight_boundary():
    assert evaluate(risk_doc(top_weight=0.40), dict(DEFAULT_POLICY))[0] == "ALLOW"
    verdict, breaches = evaluate(risk_doc(top_weight=0.41), dict(DEFAULT_POLICY))
    assert verdict == "BLOCK"
    assert breaches[0]["rule"] == "top_weight"


def test_effective_assets_floor():
    verdict, breaches = evaluate(risk_doc(effective_assets=2.5), dict(DEFAULT_POLICY))
    assert verdict == "BLOCK"
    assert breaches[0]["rule"] == "effective_assets"


def test_sector_share_cap():
    verdict, breaches = evaluate(risk_doc(sector_share=0.7), dict(DEFAULT_POLICY))
    assert verdict == "BLOCK"
    assert breaches[0]["rule"] == "sector_share"


def test_multiple_breaches_all_reported():
    doc = risk_doc(score=90, top_weight=0.5, effective_assets=2.0, sector_share=0.8)
    verdict, breaches = evaluate(doc, dict(DEFAULT_POLICY), liq_doc(days=30.0))
    assert verdict == "BLOCK"
    assert {b["rule"] for b in breaches} == {
        "score",
        "top_weight",
        "effective_assets",
        "sector_share",
        "days_to_exit",
    }
    assert len(breaches) == 5


def test_liquidity_rule_only_with_position_size():
    # Without a liquidity document the days_to_exit rule is skipped entirely.
    verdict, breaches = evaluate(risk_doc(), dict(DEFAULT_POLICY), None)
    assert verdict == "ALLOW"
    assert all(b["rule"] != "days_to_exit" for b in breaches)
    # With one, a breach is reported.
    verdict, breaches = evaluate(risk_doc(), dict(DEFAULT_POLICY), liq_doc(days=25.0))
    assert verdict == "BLOCK"
    assert breaches[0]["rule"] == "days_to_exit"


def test_missing_optional_fields_do_not_crash():
    doc = {"score": 10}  # no concentration, no sector_exposure
    verdict, breaches = evaluate(doc, dict(DEFAULT_POLICY))
    assert verdict == "ALLOW"
    assert breaches == []


def test_unknown_policy_key_raises():
    with pytest.raises(PolicyError):
        load_policy({"max_score": 50, "typo_key": 1})


def test_policy_numeric_and_range_validation():
    with pytest.raises(PolicyError):
        load_policy({"max_score": "high"})
    with pytest.raises(PolicyError):
        load_policy({"max_top_weight": 2.0})  # outside [0, 1]
    # Valid override merges cleanly.
    policy = load_policy({"max_score": 50})
    assert policy["max_score"] == 50.0
    assert policy["max_sector_share"] == DEFAULT_POLICY["max_sector_share"]


def test_max_sector_share_helper():
    assert max_sector_share(risk_doc(sector_share=0.45)) == pytest.approx(0.55)
    assert max_sector_share({}) == 0.0


def test_render_text_block_and_allow():
    verdict, breaches = evaluate(risk_doc(score=85, sector_share=0.9), dict(DEFAULT_POLICY))
    text = render_text(verdict, breaches)
    assert text.startswith("BLOCK:")
    assert "score=85" in text and "sector_share=0.9" in text
    assert render_text("ALLOW", []) == "ALLOW: every policy limit is satisfied"


def test_cli_rejects_bad_inputs(capsys):
    rc = main(["--weights", "{bad json"])
    assert rc == 2
    rc = main(["--weights", '{"NVDA":40}', "--policy", '{"bogus":1}'])
    assert rc == 2
    assert "unknown policy keys" in capsys.readouterr().err


# --- live test (skips when the API is unreachable) ---

def test_live_api_block_and_allow():
    api_base = "https://auren-api-8yrq.onrender.com"
    blocked = {
        "weights": {"NVDA": 40, "MSFT": 30, "GOOGL": 20, "ETH-USD": 10},
        "portfolio_value": 100000,
    }
    allowed = {
        "weights": {"JPM": 20, "XOM": 20, "GLD": 20, "PEP": 20, "XEL": 20},
        "portfolio_value": 50000,
    }
    try:
        risk_b = post_json(f"{api_base}/risk", {"weights": blocked["weights"]})
        liq_b = post_json(
            f"{api_base}/liquidity",
            {
                "portfolio_value": blocked["portfolio_value"],
                "weights": blocked["weights"],
            },
        )
        risk_a = post_json(f"{api_base}/risk", {"weights": allowed["weights"]})
        liq_a = post_json(
            f"{api_base}/liquidity",
            {
                "portfolio_value": allowed["portfolio_value"],
                "weights": allowed["weights"],
            },
        )
    except Exception as e:  # network down / API error -> skip, don't fail
        pytest.skip(f"AUREN API unreachable: {e}")

    verdict_b, breaches_b = evaluate(risk_b, dict(DEFAULT_POLICY), liq_b)
    verdict_a, _ = evaluate(risk_a, dict(DEFAULT_POLICY), liq_a)

    assert verdict_b == "BLOCK"
    assert {b["rule"] for b in breaches_b} >= {"score", "sector_share"}
    assert verdict_a == "ALLOW"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
