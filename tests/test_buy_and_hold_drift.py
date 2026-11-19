import pathlib
import pandas as pd
import pytest
from engine.metrics import (
    concentration,
    portfolio_returns,
    volatility,
    max_drawdown,
    correlation,
    high_pairs,
    sector_exposure,
)
from engine.score import risk_score

CACHE = pathlib.Path(__file__).parent.parent / "data" / "prices.csv"


def test_buy_and_hold_eliminates_shannons_demon_zero_vol():
    # Two oscillating assets with w = 50/50.
    # Daily constant-mix (r @ w) yields constant +25% every step -> 0% vol, 0% drawdown.
    # True buy-and-hold wealth oscillates 1.00 -> 1.25 -> 1.00 -> 1.25 (-20% drawdown, >0 vol).
    prices = pd.DataFrame({
        "A": [100.0, 200.0, 100.0, 50.0, 100.0, 200.0, 100.0, 50.0],
        "B": [100.0,  50.0, 100.0, 200.0, 100.0, 50.0, 100.0, 200.0],
    })
    w = pd.Series({"A": 0.5, "B": 0.5})

    pr_reb = portfolio_returns(prices, w, rebalance_daily=True)
    assert volatility(pr_reb) == pytest.approx(0.0)
    assert max_drawdown(pr_reb) == pytest.approx(0.0)

    pr_bh = portfolio_returns(prices, w)
    wealth = (1 + pr_bh).cumprod()
    assert wealth.iloc[-1] == pytest.approx(1.25)
    assert max_drawdown(pr_bh) == pytest.approx(-0.20)
    assert volatility(pr_bh) > 3.0


def test_single_asset_buy_and_hold_matches_rebalanced():
    prices = pd.DataFrame({"A": [100.0, 110.0, 99.0, 120.0]})
    w = pd.Series({"A": 1.0})
    pd.testing.assert_series_equal(
        portfolio_returns(prices, w),
        portfolio_returns(prices, w, rebalance_daily=True),
    )


def test_cached_mu_equal_weight_drift_triggers_vol_and_mdd_rules():
    prices = pd.read_csv(CACHE, index_col=0, parse_dates=True)
    w = pd.Series({"MU": 0.25, "COST": 0.25, "PEP": 0.25, "XEL": 0.25})
    c = concentration(w)
    pairs = high_pairs(correlation(prices, w.index))
    sec_max = float(sector_exposure(w).max())

    pr_bh = portfolio_returns(prices, w)
    vol_bh, mdd_bh = volatility(pr_bh), max_drawdown(pr_bh)
    score_bh, level_bh, _ = risk_score(c, vol_bh, mdd_bh, pairs, sec_max)

    assert vol_bh == pytest.approx(0.421839, abs=1e-4)
    assert mdd_bh == pytest.approx(-0.355056, abs=1e-4)
    assert (score_bh, level_bh) == (35, "Medium")
