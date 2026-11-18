from pathlib import Path

import pandas as pd
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from engine import data


@pytest.fixture
def clear_dashboard_cache():
    st.cache_data.clear()
    yield
    st.cache_data.clear()


@pytest.mark.parametrize("has_correlated_pair", [True, False])
def test_correlation_summary_ignores_undefined_pairs(
    monkeypatch, clear_dashboard_cache, has_correlated_pair
):
    dates = pd.bdate_range("2025-01-01", periods=31)
    prices = pd.DataFrame(
        {"NVDA": 200.0, "MSFT": 100.0, "GOOGL": 200.0, "ETH-USD": 90.0},
        index=dates,
    )
    if has_correlated_pair:
        prices["MSFT"] = range(100, 131)
        prices["GOOGL"] = prices["MSFT"] * 2

    volumes = pd.DataFrame(1_000, index=dates, columns=prices.columns)
    monkeypatch.setattr(data, "load_prices", lambda tickers: prices[tickers])
    monkeypatch.setattr(data, "load_volumes", lambda tickers: volumes[tickers])

    app_path = Path(__file__).resolve().parents[1] / "app.py"
    dashboard = AppTest.from_file(app_path, default_timeout=15).run()

    assert not dashboard.exception
    correlation_tab = next(tab for tab in dashboard.tabs if tab.label == "Correlation")
    summary = next(
        element.value for element in correlation_tab.markdown
        if "Most correlated pair" in element.value
    )
    if has_correlated_pair:
        assert "MSFT · GOOGL" in summary
        assert "Correlation 1.00" in summary
    else:
        assert "No pair has a defined correlation" in summary
        assert all("Low co-movement" not in element.value for element in correlation_tab.markdown)

    counts = next(
        element.value for element in correlation_tab.markdown
        if "Pairs above 0.7" in element.value
    )
    expected_count = int(has_correlated_pair)
    assert f"Out of {expected_count} measured pairs" in counts
