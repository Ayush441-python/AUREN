import pathlib
import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch
import streamlit as st
from streamlit.testing.v1 import AppTest

from engine.liquidity import avg_daily_value, days_to_exit
from engine.data import _cached, CACHE, VOL_CACHE

APP_PATH = pathlib.Path(__file__).parent.parent / "app.py"


def test_avg_daily_value_unrelated_missing_closes():
    """Verify that missing closing prices in one asset do not shift the
    lookback window or alter the ADV calculation for unrelated holdings."""
    dates = pd.bdate_range("2026-01-05", periods=60)
    closes = pd.DataFrame({"MSFT": 100.0, "AAPL": 50.0}, index=dates)
    volumes = pd.DataFrame(
        {"MSFT": [10_000] * 30 + [10] * 30, "AAPL": 200_000}, index=dates
    )
    positions = pd.Series({"MSFT": 6_000.0, "AAPL": 4_000.0})

    # Case 1: Both assets have all 60 closing prices
    adv_full = avg_daily_value(closes, volumes, window=30)
    dte_full = days_to_exit(positions, adv_full, participation=0.10)
    assert adv_full["MSFT"] == pytest.approx(1_000.0)
    assert dte_full["MSFT"] == pytest.approx(60.0)

    # Case 2: Only AAPL's latest 30 closing prices are missing
    closes_missing = closes.copy()
    closes_missing.loc[dates[-30:], "AAPL"] = np.nan

    # Passing raw (per-asset) price frame preserves MSFT's current window
    adv_raw = avg_daily_value(closes_missing, volumes, window=30)
    dte_raw = days_to_exit(positions, adv_raw, participation=0.10)
    assert adv_raw["MSFT"] == pytest.approx(1_000.0)
    assert dte_raw["MSFT"] == pytest.approx(60.0)

    # Note: If complete-case dropna() was used across assets, MSFT was erroneously shifted
    adv_dropped = avg_daily_value(closes_missing.dropna(), volumes, window=30)
    dte_dropped = days_to_exit(positions, adv_dropped, participation=0.10)
    assert adv_dropped["MSFT"] == pytest.approx(1_000_000.0)
    assert dte_dropped["MSFT"] == pytest.approx(0.06)


def test_avg_daily_value_crypto_denomination():
    """Verify that crypto tokens ending with -USD treat volume as USD traded directly."""
    dates = pd.bdate_range("2026-01-05", periods=30)
    closes = pd.DataFrame({"BTC-USD": 50_000.0, "MSFT": 100.0}, index=dates)
    volumes = pd.DataFrame({"BTC-USD": 5_000_000.0, "MSFT": 10_000.0}, index=dates)

    adv = avg_daily_value(closes, volumes, window=30)
    # Crypto: used as is ($5,000,000)
    assert adv["BTC-USD"] == pytest.approx(5_000_000.0)
    # Stock: price * volume = 100 * 10,000 = $1,000,000
    assert adv["MSFT"] == pytest.approx(1_000_000.0)


def test_days_to_exit_zero_and_missing_adv():
    """Verify days to exit handling when ADV is zero or missing."""
    positions = pd.Series({"A": 10_000.0, "B": 20_000.0, "C": 5_000.0})
    adv = pd.Series({"A": 0.0, "B": 100_000.0})  # C is missing

    dte = days_to_exit(positions, adv, participation=0.10)
    assert np.isnan(dte["A"])
    assert dte["B"] == pytest.approx(2.0)
    assert np.isnan(dte["C"])


def test_analyze_keeps_both_raw_and_complete_case_frames():
    """Verify analyze() returns complete-case prices and original per-asset prices."""
    from app import analyze

    dates = pd.bdate_range("2026-01-05", periods=60)
    closes_missing = pd.DataFrame({"MSFT": 100.0, "AAPL": 50.0}, index=dates)
    closes_missing.loc[dates[-30:], "AAPL"] = np.nan

    weights = pd.Series({"MSFT": 0.6, "AAPL": 0.4})

    with patch("app.get_prices", return_value=closes_missing):
        result = analyze(weights)

    assert result is not None
    assert "prices" in result
    assert "raw_prices" in result
    assert "per_asset_prices" in result

    # prices is complete-case (dropped AAPL's missing dates)
    assert len(result["prices"]) == 30
    assert not result["prices"].isna().any().any()

    # raw_prices preserves all rows per asset
    assert len(result["raw_prices"]) == 60
    assert result["raw_prices"]["MSFT"].notna().sum() == 60


def test_streamlit_app_liquidity_replay():
    """Streamlit AppTest replay: Verifies that in the rendered Liquidity tab,
    removing latest 30 AAPL closes does not shift MSFT's metrics."""
    dates = pd.bdate_range("2026-01-05", periods=60)
    closes_full = pd.DataFrame({"MSFT": 100.0, "AAPL": 50.0}, index=dates)
    volumes = pd.DataFrame(
        {"MSFT": [10_000] * 30 + [10] * 30, "AAPL": 200_000}, index=dates
    )

    closes_missing = closes_full.copy()
    closes_missing.loc[dates[-30:], "AAPL"] = np.nan

    pf_df = pd.DataFrame(
        [{"ticker": "MSFT", "weight": 60.0}, {"ticker": "AAPL", "weight": 40.0}]
    )

    def make_load_prices(custom_closes):
        def _mock(tickers, period="2y"):
            if set(tickers) == {"AAPL", "MSFT"}:
                return custom_closes[sorted(tickers)]
            return _cached(CACHE, tickers)

        return _mock

    def mock_volumes(tickers, period="2y"):
        if set(tickers) == {"AAPL", "MSFT"}:
            return volumes[sorted(tickers)]
        return _cached(VOL_CACHE, tickers)

    # Run 1: Both assets have all 60 closing prices
    with patch(
        "engine.data.load_prices", side_effect=make_load_prices(closes_full)
    ), patch("engine.data.load_volumes", side_effect=mock_volumes):
        st.cache_data.clear()
        at1 = AppTest.from_file(APP_PATH)
        at1.run()
        at1.selectbox[0].select("Custom / Edited")
        at1.session_state["pf_df"] = pf_df
        at1.session_state["pf_v"] += 1
        at1.run()
        liq1 = [
            df.value for df in at1.dataframe if "Days to Exit" in df.value.columns
        ][0]

    # Run 2: Missing AAPL closes
    with patch(
        "engine.data.load_prices", side_effect=make_load_prices(closes_missing)
    ), patch("engine.data.load_volumes", side_effect=mock_volumes):
        st.cache_data.clear()
        at2 = AppTest.from_file(APP_PATH)
        at2.run()
        at2.selectbox[0].select("Custom / Edited")
        at2.session_state["pf_df"] = pf_df
        at2.session_state["pf_v"] += 1
        at2.run()
        liq2 = [
            df.value for df in at2.dataframe if "Days to Exit" in df.value.columns
        ][0]

    msft1 = liq1[liq1["Ticker"] == "MSFT"].iloc[0]
    msft2 = liq2[liq2["Ticker"] == "MSFT"].iloc[0]

    assert msft1["30D Daily Traded ($)"] == pytest.approx(1_000.0)
    assert msft1["Days to Exit"] == pytest.approx(60.0)
    assert msft1["Liquidity Status"] == "Illiquid (1d+)"

    assert msft2["30D Daily Traded ($)"] == pytest.approx(1_000.0)
    assert msft2["Days to Exit"] == pytest.approx(60.0)
    assert msft2["Liquidity Status"] == "Illiquid (1d+)"
