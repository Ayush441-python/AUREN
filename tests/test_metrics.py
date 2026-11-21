import itertools
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


def test_sector_exposure_boundary_permutations_issue_133():
    # Issue #133: NVDA (17%), MSFT (28%), AAPL (5%) in Big Tech (total 50%)
    # AMD (25%), TSM (25%) in AI & Semiconductors (total 50%)
    # All 6 permutations of Big Tech holdings must not trigger the spurious +15 sector penalty.
    big_tech_assets = [("NVDA", 0.17), ("MSFT", 0.28), ("AAPL", 0.05)]
    ai_semi_assets = [("AMD", 0.25), ("TSM", 0.25)]

    for perm in itertools.permutations(big_tech_assets):
        holdings = list(perm) + ai_semi_assets
        tickers, weights = zip(*holdings)
        w = pd.Series(weights, index=tickers)

        exp = sector_exposure(w)
        assert exp["Big Tech"] == pytest.approx(0.50)
        assert exp["AI & Semiconductors"] == pytest.approx(0.50)
        assert float(exp.max()) <= 0.50

        c = concentration(w)
        # Max weight 28% <= 30%, effective assets > 4, no pairs, no qualifying drawdown
        # Controlled volatility at 31% contributes +20
        score, level, hits = risk_score(
            c, vol=0.31, mdd=-0.10, pairs=[], sector_max=float(exp.max())
        )
        assert score == 20
        assert level == "Low"
        assert len(hits) == 1
        assert hits[0][0] == 20
        assert "Volatility" in hits[0][1]
        assert not any("sector" in why for _, why in hits)


def test_sector_exposure_strictly_greater_than_50_percent_threshold():
    # Strict rule: "More than 50% sits in one sector" (+15 points)
    # Test 49.99%, exactly 50%, floating-point noise at 50%, and 50.01%
    conc = {"top_weight": 0.20, "effective_assets": 5.0}

    # 49.99%: Should not trigger penalty
    score_4999, level_4999, hits_4999 = risk_score(
        conc, vol=0.10, mdd=-0.05, pairs=[], sector_max=0.4999
    )
    assert score_4999 == 0
    assert level_4999 == "Low"
    assert hits_4999 == []

    # Exactly 50%: Should not trigger penalty
    score_50, level_50, hits_50 = risk_score(
        conc, vol=0.10, mdd=-0.05, pairs=[], sector_max=0.50
    )
    assert score_50 == 0
    assert level_50 == "Low"
    assert hits_50 == []

    # Floating point noise around 50% (e.g. 0.5000000000000001): Should not trigger penalty
    score_50_fp, level_50_fp, hits_50_fp = risk_score(
        conc, vol=0.10, mdd=-0.05, pairs=[], sector_max=0.5000000000000001
    )
    assert score_50_fp == 0
    assert level_50_fp == "Low"
    assert hits_50_fp == []

    # 50.01%: Strictly greater than 50%, should trigger +15 penalty
    score_5001, level_5001, hits_5001 = risk_score(
        conc, vol=0.10, mdd=-0.05, pairs=[], sector_max=0.5001
    )
    assert score_5001 == 15
    assert level_5001 == "Low"
    assert len(hits_5001) == 1
    assert hits_5001[0][0] == 15
    assert "sector" in hits_5001[0][1]


def test_portfolio_boundary_thresholds_49_50_51():
    conc_safe = {"top_weight": 0.20, "effective_assets": 5.0}

    # 49.99% group exposure portfolio: no sector penalty
    w_4999 = pd.Series([0.4999, 0.30, 0.2001], index=["NVDA", "AMD", "GLD"])
    exp_4999 = sector_exposure(w_4999)
    assert exp_4999.max() == pytest.approx(0.4999)
    score_4999, _, hits_4999 = risk_score(
        conc_safe, vol=0.10, mdd=-0.05, pairs=[], sector_max=float(exp_4999.max())
    )
    assert not any("sector" in why for _, why in hits_4999)

    # 50.00% group exposure portfolio: no sector penalty
    w_50 = pd.Series([0.50, 0.50], index=["NVDA", "AMD"])
    exp_50 = sector_exposure(w_50)
    assert exp_50.max() == pytest.approx(0.50)
    score_50, _, hits_50 = risk_score(
        conc_safe, vol=0.10, mdd=-0.05, pairs=[], sector_max=float(exp_50.max())
    )
    assert not any("sector" in why for _, why in hits_50)

    # 50.01% group exposure portfolio: triggers +15 sector penalty
    w_5001 = pd.Series([0.5001, 0.25, 0.2499], index=["NVDA", "AMD", "GLD"])
    exp_5001 = sector_exposure(w_5001)
    assert exp_5001.max() == pytest.approx(0.5001)
    score_5001, _, hits_5001 = risk_score(
        conc_safe, vol=0.10, mdd=-0.05, pairs=[], sector_max=float(exp_5001.max())
    )
    assert any("sector" in why for _, why in hits_5001)
    assert score_5001 == 15
