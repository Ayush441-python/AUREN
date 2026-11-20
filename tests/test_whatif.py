from pathlib import Path
from unittest.mock import patch
import pandas as pd
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def clear_streamlit_cache():
    st.cache_data.clear()
    yield
    st.cache_data.clear()


def test_whatif_repro_window_fixed():
    """Verify Issue #145: What-if comparison runs on common lookback window."""
    dates = pd.read_csv(ROOT / "data/prices.csv", index_col=0, parse_dates=True)[
        "MSFT"
    ].dropna().index[:60]
    prices = pd.DataFrame(
        {
            "MSFT": [100.0] * 10 + [60.0] * 50,
            "AAPL": [float("nan")] * 20 + [60.0] * 40,
        },
        index=dates,
    )
    volumes = pd.DataFrame(100_000.0, index=dates, columns=prices.columns)

    def holdings(frame, **kwargs):
        ticker = "AAPL" if kwargs["key"].startswith("pfb_") else "MSFT"
        return pd.DataFrame({"ticker": [ticker], "weight": [100.0]})

    observed = {}
    orig_plot = st.plotly_chart

    def capture(figure, *args, **kwargs):
        if [trace.name for trace in figure.data] == ["Current", "What-if"]:
            for t in figure.data:
                observed[t.name] = (
                    pd.Timestamp(t.x[0]).date(),
                    len(t.x),
                    round(float(min(t.y)), 8),
                )
        return orig_plot(figure, *args, **kwargs)

    with patch("engine.data.load_prices", side_effect=lambda tickers: prices[tickers]), \
         patch("engine.data.load_volumes", side_effect=lambda tickers: volumes[tickers]), \
         patch.object(st, "data_editor", side_effect=holdings), \
         patch.object(st, "plotly_chart", side_effect=capture):
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=45).run()
        assert not app.exception, [e.value for e in app.exception]

    # Both traces should start on the exact same date (2024-12-18) and have 39 observations
    first_common_return = pd.Timestamp("2024-12-18").date()
    assert observed["Current"] == (first_common_return, 39, 0.0)
    assert observed["What-if"] == (first_common_return, 39, 0.0)

    # What-if cards should reflect identical scores and delta 0
    markdowns = [m.value for m in app.markdown]
    assert any('<div class="label">Current score</div><div class="value">50</div>' in m for m in markdowns)
    assert any('<div class="label">What-if score</div><div class="value gold">50</div>' in m for m in markdowns)
    assert any('<div class="label">Delta</div><div class="value">+0</div>' in m for m in markdowns)

    # Standalone full-history metrics are preserved outside the comparison (sidebar shows 85)
    sidebar_scores = [m.value for m in app.sidebar.markdown if "Risk score" in m.value]
    assert any("85" in s and "High Risk" in s for s in sidebar_scores)


def test_whatif_too_few_shared_prices():
    """Verify warning when shared history is under 30 trading sessions."""
    dates = pd.read_csv(ROOT / "data/prices.csv", index_col=0, parse_dates=True)[
        "MSFT"
    ].dropna().index[:60]
    prices = pd.DataFrame(
        {
            "MSFT": [100.0] * 60,
            "AAPL": [float("nan")] * 40 + [60.0] * 20,
        },
        index=dates,
    )
    volumes = pd.DataFrame(100_000.0, index=dates, columns=prices.columns)

    def holdings(frame, **kwargs):
        ticker = "AAPL" if kwargs["key"].startswith("pfb_") else "MSFT"
        return pd.DataFrame({"ticker": [ticker], "weight": [100.0]})

    with patch("engine.data.load_prices", side_effect=lambda tickers: prices[tickers]), \
         patch("engine.data.load_volumes", side_effect=lambda tickers: volumes[tickers]), \
         patch.object(st, "data_editor", side_effect=holdings):
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=45).run()
        assert not app.exception, [e.value for e in app.exception]

    errors = [e.value for e in app.error]
    assert any("Too few shared prices to compare portfolios" in e for e in errors)
