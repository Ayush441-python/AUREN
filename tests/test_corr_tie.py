"""Regression tests for exact Pearson ties at the 0.7 threshold (#164)."""
from itertools import permutations

import numpy as np
import pandas as pd

from engine.metrics import (concentration, high_pairs, max_drawdown,
                            portfolio_returns, sector_exposure, volatility)
from engine.score import risk_score


def _fixture():
    w = pd.Series({'AAPL': .5, 'MSFT': .25, 'COST': .125, 'GLD': .125})
    a = np.array([2, 1, -1, -2, 0, 0] + [0] * 24)
    b = np.array([0, 2, -1, -2, 0, 1] + [0] * 24)
    r = np.column_stack((a, a, b, -a)) / 64
    prices = pd.DataFrame(
        64 * np.vstack([np.ones(4), (1 + r).cumprod(axis=0)]),
        columns=w.index)
    return w, prices


def test_exact_seven_tenths_tie_is_order_independent():
    """corr == exactly 7/10 must not be flagged in any ticker order."""
    w, prices = _fixture()
    for order in permutations(w.index):
        weights = w.loc[list(order)]
        rets = prices[list(order)].dropna().pct_change().dropna()
        pairs = high_pairs(rets.corr(), returns=rets)
        # Only AAPL/MSFT (r = 1) may be flagged.
        assert len(pairs) == 1 and set(pairs[0][:2]) == {"AAPL", "MSFT"}


def test_genuinely_above_threshold_still_flagged():
    idx = pd.bdate_range("2024-01-01", periods=40)
    x = np.sin(np.arange(40))
    y = x + np.random.default_rng(0).normal(0, 0.01, 40)
    rets = pd.DataFrame({"X": x, "Y": y}, index=idx)
    corr = rets.corr()
    pairs = high_pairs(corr, returns=rets)
    assert any(set(p[:2]) == {"X", "Y"} for p in pairs)


def test_below_threshold_not_flagged():
    rng = np.random.default_rng(1)
    rets = pd.DataFrame(rng.normal(size=(60, 2)), columns=["P", "Q"])
    corr = rets.corr()
    pairs = high_pairs(corr, returns=rets)
    assert not any(set(p[:2]) == {"P", "Q"} for p in pairs)
