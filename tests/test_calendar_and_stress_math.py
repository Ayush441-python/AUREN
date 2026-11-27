import numpy as np
import pandas as pd
import pytest

from engine.data import CACHE
from engine.metrics import correlation, portfolio_returns, volatility
from engine.score import risk_score
from engine.stress import worst_periods


def test_volatility_no_weekend_ffill_cliff():
    """Forward-filling equities across weekends on a 365-day calendar must not
    deflate annualized volatility by sqrt(252/365) (~16.9%)."""
    idx = pd.date_range("2025-01-01", periods=365, freq="D")
    rng = np.random.default_rng(42)
    eq_rets = rng.normal(0.0, 0.02, size=len(idx))
    eq_prices = 100.0 * np.cumprod(1.0 + eq_rets)

    # Simulate 5-day stock market (NaN on Sat/Sun) and 7-day crypto
    df = pd.DataFrame(
        {
            "NVDA": eq_prices,
            "BTC-USD": 100.0 * np.cumprod(1.0 + rng.normal(0.0, 0.03, size=len(idx))),
        },
        index=idx,
    )
    df.loc[df.index.day_of_week >= 5, "NVDA"] = np.nan

    eq_only_pr = portfolio_returns(df[["NVDA"]].dropna(), pd.Series({"NVDA": 1.0}))
    mixed_aligned = df.ffill(limit=3).dropna()
    mixed_pr = portfolio_returns(
        mixed_aligned, pd.Series({"NVDA": 0.9999, "BTC-USD": 0.0001})
    )

    vol_eq = volatility(eq_only_pr)
    vol_mixed = volatility(mixed_pr)
    # Must remain consistent (~31% -> ~31%) rather than dropping by 16.9%
    assert abs(vol_mixed - vol_eq) < 0.02


def test_cached_googl_retains_above_30pct_volatility_penalty():
    """In data/prices.csv, GOOGL true trading-day volatility (~33.3%) exceeds 30%;
    calendar-padded computation must still exceed 30% rather than dropping to 27.6%."""
    prices = pd.read_csv(CACHE, index_col=0, parse_dates=True)
    true_pr = portfolio_returns(prices[["GOOGL"]].dropna(), pd.Series({"GOOGL": 1.0}))
    cal_pr = portfolio_returns(
        prices[["GOOGL"]].ffill(limit=3).dropna(), pd.Series({"GOOGL": 1.0})
    )
    assert volatility(true_pr) > 0.30
    assert volatility(cal_pr) > 0.30
    score, _, hits = risk_score(
        {"top_weight": 1.0, "effective_assets": 1.0},
        volatility(cal_pr),
        -0.10,
        [],
        1.0,
    )
    assert any("Volatility is" in msg for _, msg in hits)
    assert score >= 70


def test_correlation_ignores_weekend_equity_plateaus():
    """Adding a 7-day crypto asset must not distort equity-equity correlation or
    attenuate equity-crypto correlation with flat 0.0 weekend equity returns."""
    prices = pd.read_csv(CACHE, index_col=0, parse_dates=True)
    c_eq_only = correlation(prices[["NVDA", "AMD"]].dropna(), ["NVDA", "AMD"])
    mixed = prices[["NVDA", "AMD", "BTC-USD", "ETH-USD"]].ffill(limit=3).dropna()
    c_mixed = correlation(mixed, ["NVDA", "AMD", "BTC-USD", "ETH-USD"])

    # Equity-equity pair remains virtually identical despite 208 weekend rows
    assert c_mixed.loc["NVDA", "AMD"] == pytest.approx(
        c_eq_only.loc["NVDA", "AMD"], abs=1e-4
    )
    # 7-day crypto-crypto correlation preserves all calendar observations cleanly
    c_crypto_only = correlation(
        prices.loc[mixed.index.min() :, ["BTC-USD", "ETH-USD"]].dropna(),
        ["BTC-USD", "ETH-USD"],
    )
    assert c_mixed.loc["BTC-USD", "ETH-USD"] == pytest.approx(
        c_crypto_only.loc["BTC-USD", "ETH-USD"], abs=1e-12
    )
    # Equity-crypto correlation is not attenuated by ~17% via flat 0.0 weekend rows
    assert c_mixed.loc["NVDA", "BTC-USD"] > 0.31


def test_worst_periods_uses_30_day_window_on_calendar_index():
    """A calendar-padded index uses a 30-day (1 calendar month) rolling window while
    a trading-day index uses 21 trading days."""
    cal_idx = pd.date_range("2025-01-01", periods=60, freq="D")
    # Two -10% drops 25 calendar days apart (~3.5 weeks, within one calendar month)
    rets = pd.Series(0.0, index=cal_idx)
    rets.iloc[5] = -0.10
    rets.iloc[30] = -0.10
    wp = worst_periods(rets)
    assert wp["worst_day"] == pytest.approx(-0.10)
    assert wp["worst_month"] == pytest.approx(-0.19)  # 0.9 * 0.9 - 1
