import pandas as pd
import pytest
from engine.metrics import (
    concentration,
    volatility,
    max_drawdown,
    correlation,
    high_pairs,
    sector_exposure,
)
from engine.score import risk_score
from engine.stress import stress


def test_equal_weights_effective_assets():
    w = pd.Series([0.25] * 4, index=list("ABCD"))
    assert concentration(w)["effective_assets"] == pytest.approx(4)


def test_drawdown_known_case():
    pr = pd.Series([0.10, -0.50, 0.20])  # 1.10 -> 0.55 -> 0.66
    assert max_drawdown(pr) == pytest.approx(-0.5)


def test_no_swings_no_volatility():
    assert volatility(pd.Series([0.01] * 10)) == pytest.approx(0)


def test_perfectly_correlated_assets():
    prices = pd.DataFrame(
        {"A": [100, 101, 103, 102, 105], "B": [200, 202, 206, 204, 210]}
    )  # B = 2 x A
    corr = correlation(prices, ["A", "B"])
    assert corr.loc["A", "B"] == pytest.approx(1.0)


def test_high_pairs_finds_the_pair():
    prices = pd.DataFrame(
        {"A": [100, 101, 103, 102, 105], "B": [200, 202, 206, 204, 210]}
    )
    corr = correlation(prices, ["A", "B"])
    assert high_pairs(corr) == [("A", "B", 1.0)]


def test_safe_portfolio_scores_zero():
    conc = {"top_weight": 0.10, "effective_assets": 10}
    score, level, hits = risk_score(conc, 0.10, -0.05, [], 0.20)
    assert score == 0 and level == "Low" and hits == []


def test_worst_case_scores_100():
    conc = {"top_weight": 0.60, "effective_assets": 1.5}
    pairs = [("A", "B", 0.9), ("A", "C", 0.8)]
    score, level, hits = risk_score(conc, 0.50, -0.50, pairs, 0.80)
    assert score == 100 and level == "High"


def test_single_rule_adds_its_points():
    conc = {"top_weight": 0.40, "effective_assets": 10}
    score, _, hits = risk_score(conc, 0.10, -0.05, [], 0.20)
    assert score == 20 and len(hits) == 1


def test_sector_exposure_tech():
    # Day 9 test from playbook: NVDA 50% + MSFT 50% gives Big Tech = 100%
    w = pd.Series([0.5, 0.5], index=["NVDA", "MSFT"])
    exp = sector_exposure(w)
    assert exp.get("Big Tech", 0) == pytest.approx(1.0)


def test_stress_scenario():
    # Day 11 test from playbook: 50% NVDA + 50% GLD in "Big Tech falls 20%" = -10%
    w = pd.Series([0.5, 0.5], index=["NVDA", "GLD"])
    shocks = {"Big Tech": -0.20}
    assert stress(w, shocks) == pytest.approx(-0.10)


def test_exact_thirty_percent_concentration_boundary():
    # Exactly 30% concentration should not trigger "over 30%" rule (+20 pts)
    # even with float representation drift
    conc_exact = {"top_weight": 0.30, "effective_assets": 4.5}
    conc_drift = {"top_weight": 0.30000000000000004, "effective_assets": 4.5}
    conc_over = {"top_weight": 0.3001, "effective_assets": 4.5}

    score_exact, _, hits_exact = risk_score(conc_exact, 0.10, -0.05, [], 0.20)
    score_drift, _, hits_drift = risk_score(conc_drift, 0.10, -0.05, [], 0.20)
    score_over, _, hits_over = risk_score(conc_over, 0.10, -0.05, [], 0.20)

    assert score_exact == 0 and len(hits_exact) == 0
    assert score_drift == 0 and len(hits_drift) == 0
    assert score_over == 20 and len(hits_over) == 1
    assert "over 30%" in hits_over[0][1]


def test_api_risk_unit_invariance_for_thirty_percent():
    from unittest.mock import patch
    from fastapi.testclient import TestClient
    import api

    p = pd.read_csv("data/prices.csv", index_col=0, parse_dates=True)
    with patch.object(api, "load_prices", side_effect=lambda k, **kwargs: p[k]), TestClient(api.app) as c:
        # Both percentage inputs (30%) and fractional inputs (0.3) must produce identical 15 Low scores
        r_pct = c.post("/risk", json={"weights": {"GLD": 30, "COST": 27.5, "JPM": 20, "XOM": 22.5}}).json()
        r_frac = c.post("/risk", json={"weights": {"GLD": 0.3, "COST": 0.275, "JPM": 0.2, "XOM": 0.225}}).json()
        r_ctrl = c.post("/risk", json={"weights": {"GLD": 30.01, "COST": 27.49, "JPM": 20, "XOM": 22.5}}).json()

        assert r_pct["score"] == 15 and r_pct["level"] == "Low"
        assert r_frac["score"] == 15 and r_frac["level"] == "Low"
        assert r_pct["concentration"]["top_weight"] == pytest.approx(0.30)
        assert r_frac["concentration"]["top_weight"] == pytest.approx(0.30)
        assert r_ctrl["score"] == 35 and r_ctrl["level"] == "Medium"

