import math

import numpy as np
import pandas as pd
import pytest
from engine.metrics import (
    concentration,
    correlation,
    drawdown_series,
    high_pairs,
    max_drawdown,
    sector_exposure,
    volatility,
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


def test_max_drawdown_day1_crash_partial_recovery():
    # Portfolio starts at 1.0, drops 35% on Day 1 to 0.65, then rallies monotonically
    # without ever reaching 1.0 again. Must report -0.35, not 0.0.
    pr = pd.Series([-0.35, 0.10, 0.10])  # 1.00 -> 0.65 -> 0.715 -> 0.7865
    assert max_drawdown(pr) == pytest.approx(-0.35)
    assert drawdown_series(pr).tolist() == pytest.approx([-0.35, -0.285, -0.2135])


def test_max_drawdown_day1_crash_secondary_dip_above_day1_low():
    # Day-1 trough (0.65) is deeper than Day-3 dip (0.710125).
    pr = pd.Series([-0.35, 0.15, -0.05])
    dd = drawdown_series(pr)
    assert dd.idxmin() == 0
    assert max_drawdown(pr) == pytest.approx(-0.35)


def test_max_drawdown_monotonic_loss_from_day1():
    pr = pd.Series([-0.10, -0.10, -0.10])  # 1.0 -> 0.9 -> 0.81 -> 0.729
    assert drawdown_series(pr).tolist() == pytest.approx([-0.10, -0.19, -0.271])
    assert max_drawdown(pr) == pytest.approx(-0.271)


def test_max_drawdown_recovery_past_initial_peak_then_deeper_drop():
    # Drops -20% (0.80), recovers above 1.0 to 1.20 (+50%), then drops -40% to 0.72.
    pr = pd.Series([-0.20, 0.50, -0.40])
    assert drawdown_series(pr).tolist() == pytest.approx([-0.20, 0.0, -0.40])
    assert max_drawdown(pr) == pytest.approx(-0.40)


def test_max_drawdown_flat_and_strictly_positive_returns():
    flat = pd.Series([0.0, 0.0, 0.0])
    assert max_drawdown(flat) == pytest.approx(0.0)
    assert drawdown_series(flat).tolist() == pytest.approx([0.0, 0.0, 0.0])

    rising = pd.Series([0.02, 0.05, 0.01])
    assert max_drawdown(rising) == pytest.approx(0.0)
    assert drawdown_series(rising).tolist() == pytest.approx([0.0, 0.0, 0.0])


def test_max_drawdown_single_day():
    assert max_drawdown(pd.Series([-0.25])) == pytest.approx(-0.25)
    assert max_drawdown(pd.Series([0.25])) == pytest.approx(0.0)


def test_max_drawdown_total_wipeout_avoids_zero_division():
    pr = pd.Series([-1.0, 0.0])
    dd = drawdown_series(pr)
    assert dd.tolist() == pytest.approx([-1.0, -1.0])
    assert max_drawdown(pr) == pytest.approx(-1.0)


def test_max_drawdown_empty_and_nan_conventions():
    empty = pd.Series([], dtype=float)
    assert drawdown_series(empty).empty
    assert math.isnan(max_drawdown(empty))

    all_nan = pd.Series([np.nan, np.nan], dtype=float)
    assert math.isnan(max_drawdown(all_nan))

    with_nan = pd.Series([-0.20, np.nan, 0.10])
    assert max_drawdown(with_nan) == pytest.approx(-0.20)
    assert drawdown_series(with_nan).iloc[2] == pytest.approx(-0.12)


@pytest.mark.parametrize(
    "returns",
    [
        [-0.35, 0.10, 0.10, 0.05],
        [-0.05, -0.15, 0.30, -0.10, -0.20],
        [0.10, 0.20, -0.25, 0.40, -0.50],
        [0.0, -0.01, 0.01, 0.0],
    ],
)
def test_drawdown_series_mathematical_invariants(returns):
    pr = pd.Series(returns)
    dd = drawdown_series(pr)

    # Invariant 1: matches explicit 1.0-prepended equity curve cummax formula
    equity = pd.concat([pd.Series([1.0]), (1 + pr).cumprod()], ignore_index=True)
    expected = (equity / equity.cummax() - 1).iloc[1:].reset_index(drop=True)
    assert dd.tolist() == pytest.approx(expected.tolist())

    # Invariant 2: bounded in [-1.0, 0.0] and minimum equals max_drawdown
    assert (dd <= 0.0).all() and (dd >= -1.0).all()
    assert float(dd.min()) == pytest.approx(max_drawdown(pr))
