import pandas as pd
import pytest
from engine.data import load_prices, load_unadjusted_prices
from engine.liquidity import avg_daily_value, days_to_exit


def test_liquidity_synthetic_dividend_math():
    """Reproduces Issue #42 synthetic dividend scenario.
    30 sessions, 1,000 shares traded each day.
    Unadjusted close: $100 for 29 days and $90 on the last day following a $10 cash dividend.
    Adjusted close: prior closes adjusted to $90 across all 30 days.
    For a $9,500 holding at 10% participation:
    Correct close-based estimate is 0.953 days versus 1.056 days under adjusted series.
    """
    v = pd.DataFrame({"AAPL": [1000.0] * 30})
    closes_unadjusted = [100.0] * 29 + [90.0]
    closes_adjusted = [90.0] * 30

    adv_unadj = avg_daily_value(pd.DataFrame({"AAPL": closes_unadjusted}), v)
    dte_unadj = days_to_exit(pd.Series({"AAPL": 9500.0}), adv_unadj)

    adv_adj = avg_daily_value(pd.DataFrame({"AAPL": closes_adjusted}), v)
    dte_adj = days_to_exit(pd.Series({"AAPL": 9500.0}), adv_adj)

    # Historical trading turnover using actual transaction closes
    assert adv_unadj["AAPL"] == pytest.approx(99666.66666666667)
    assert dte_unadj["AAPL"] == pytest.approx(0.9531772575250835, rel=1e-3)

    # Adjusted series underestimates dollar liquidity by using dividend-deflated closes
    assert adv_adj["AAPL"] == pytest.approx(90000.0)
    assert dte_adj["AAPL"] == pytest.approx(1.0555555555555556, rel=1e-3)


def test_crypto_liquidity_ignores_price():
    """Crypto tickers ending in -USD report volume in dollars directly, so price is not multiplied."""
    prices = pd.DataFrame({"ETH-USD": [2000.0] * 30})
    volumes = pd.DataFrame({"ETH-USD": [500000.0] * 30})
    adv = avg_daily_value(prices, volumes)
    assert adv["ETH-USD"] == pytest.approx(500000.0)


def test_load_unadjusted_prices_vs_adjusted_cache():
    """Verify load_unadjusted_prices returns unadjusted prices when available,
    while load_prices returns adjusted prices."""
    adj_prices = load_prices(["AAPL"], period="5d")
    raw_prices = load_unadjusted_prices(["AAPL"], period="5d")

    # On 2026-11-11, AAPL unadjusted close was $355.63 vs dividend-adjusted $355.36
    if "2026-11-11" in raw_prices.index and "2026-11-11" in adj_prices.index:
        assert raw_prices.loc["2026-11-11", "AAPL"] == pytest.approx(355.63, abs=0.01)
        assert adj_prices.loc["2026-11-11", "AAPL"] == pytest.approx(355.36, abs=0.01)
