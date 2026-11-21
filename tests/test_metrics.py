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
from engine.stress import stress, worst_periods


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


def test_worst_periods_short_series():
    # When len(pr) < 21, worst_month bounds window to len(pr) and does not return NaN
    pr = pd.Series([-0.02, 0.01, -0.03])
    res = worst_periods(pr)
    assert not pd.isna(res["worst_month"])
    assert res["worst_day"] == pytest.approx(-0.03)
    # (1 - 0.02) * (1 + 0.01) * (1 - 0.03) - 1 = -0.039894
    assert res["worst_month"] == pytest.approx(-0.039894, abs=1e-5)


def test_worst_periods_single_observation():
    pr = pd.Series([-0.05])
    res = worst_periods(pr)
    assert res["worst_day"] == pytest.approx(-0.05)
    assert res["worst_month"] == pytest.approx(-0.05)


def test_worst_periods_empty_and_none():
    res_empty = worst_periods(pd.Series([], dtype=float))
    assert pd.isna(res_empty["worst_day"])
    assert pd.isna(res_empty["worst_month"])

    res_none = worst_periods(None)
    assert pd.isna(res_none["worst_day"])
    assert pd.isna(res_none["worst_month"])


def test_worst_periods_full_month():
    # 25 observations: window is 21
    pr = pd.Series([0.0] * 25)
    pr.iloc[5] = -0.10
    res = worst_periods(pr)
    assert res["worst_day"] == pytest.approx(-0.10)
    assert res["worst_month"] == pytest.approx(-0.10)


def test_rebased_portfolio_convex_hull():
    # Buy-and-hold rebased portfolio stays inside convex hull of constituent assets
    prices = pd.DataFrame({
        "A": [100.0, 200.0, 100.0],
        "B": [100.0, 100.0, 100.0]
    })
    w = pd.Series({"A": 0.5, "B": 0.5})
    norm = prices / prices.iloc[0] * 100
    rebased_portfolio = norm[w.index] @ w
    assert list(rebased_portfolio) == [100.0, 150.0, 100.0]


def test_rebased_portfolio_default_data():
    p = pd.read_csv("data/prices.csv", index_col=0, parse_dates=True)
    w = pd.Series({"NVDA": 0.4, "MSFT": 0.3, "GOOGL": 0.2, "ETH-USD": 0.1})
    clean_p = p[list(w.index)].dropna()
    norm = clean_p / clean_p.iloc[0] * 100
    rebased_portfolio = norm[w.index] @ w

    assert len(rebased_portfolio) == len(norm)
    assert rebased_portfolio.iloc[0] == pytest.approx(100.0)
    assert round(float(rebased_portfolio.iloc[-1]), 4) == 120.9186

