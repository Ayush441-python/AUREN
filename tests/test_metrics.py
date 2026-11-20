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


# --- Issue #133: exactly 50% in a broad group must not trip the >50% rule ---

_BALANCED = {"NVDA": 0.17, "MSFT": 0.28, "AAPL": 0.05, "AMD": 0.25, "TSM": 0.25}
_BIG_TECH = ["NVDA", "MSFT", "AAPL"]


@pytest.mark.parametrize("order", list(itertools.permutations(_BIG_TECH)))
def test_exact_half_group_is_order_independent(order):
    # Big Tech = 17 + 28 + 5 = 50%, AI & Semis = 25 + 25 = 50%. Entering the
    # Big Tech names in any order must give exactly 0.5, never 0.5 + 1 ULP.
    tickers = list(order) + ["AMD", "TSM"]
    w = pd.Series({t: _BALANCED[t] for t in tickers}, dtype=float)
    w = w / w.sum()
    assert float(sector_exposure(w).max()) == 0.5


@pytest.mark.parametrize("order", list(itertools.permutations(_BIG_TECH)))
def test_exact_half_group_scores_low_in_every_order(order):
    # Only the controlled 31% volatility should score: 20 points, Low.
    tickers = list(order) + ["AMD", "TSM"]
    w = pd.Series({t: _BALANCED[t] for t in tickers}, dtype=float)
    w = w / w.sum()
    conc = {"top_weight": 0.28, "effective_assets": 4.6}
    score, level, hits = risk_score(
        conc, 0.31, -0.10, [], float(sector_exposure(w).max())
    )
    assert (score, level) == (20, "Low")
    assert not any("sits in one sector" in why for _, why in hits)


@pytest.mark.parametrize(
    "sector_max, expected",
    [(0.4999, 0), (0.50, 0), (0.5001, 15)],
)
def test_only_strictly_over_half_triggers_the_sector_rule(sector_max, expected):
    conc = {"top_weight": 0.10, "effective_assets": 10}
    score, _, _ = risk_score(conc, 0.10, -0.05, [], sector_max)
    assert score == expected
