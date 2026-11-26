from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("daily_dollars", "expected_days", "expected_notice"),
    [
        (0.0, float("inf"), "Zero modeled trading capacity"),
        (None, None, "exit time is unknown"),
        (100.0, 400.0, "Liquidity Notice"),
        (40000.0, 1.0, "at least 1 trading day"),
        (80000.0, 0.5, "All portfolio positions can be fully liquidated in under 1 trading day"),
    ],
)
def test_portfolio_exit_notice(daily_dollars, expected_days, expected_notice):
    prices = pd.read_csv(ROOT / "data/prices.csv", index_col=0, parse_dates=True)
    volumes = pd.read_csv(ROOT / "data/volume.csv", index_col=0, parse_dates=True)
    # The default portfolio holds $4,000 of NVDA. Fix its price and volume
    # so the one-day boundary is exact and the other holdings are unchanged.
    prices["NVDA"] = 100.0
    if daily_dollars is None:
        volumes = volumes.drop(columns="NVDA")
    else:
        volumes["NVDA"] = daily_dollars / 100.0

    st.cache_data.clear()
    try:
        with (
            patch("engine.data.load_prices", side_effect=lambda tickers: prices[tickers]),
            patch("engine.data.load_volumes", side_effect=lambda tickers: volumes.filter(items=tickers)),
        ):
            app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=30)
        assert not list(app.exception)
        table = next(view.value for view in app.dataframe if "Days to Exit" in view.value)
        days = table.set_index("Ticker").at["NVDA", "Days to Exit"]
        if expected_days is None:
            assert pd.isna(days)
        else:
            assert days == expected_days
        assert any(expected_notice in block.value for block in app.markdown)
    finally:
        st.cache_data.clear()
