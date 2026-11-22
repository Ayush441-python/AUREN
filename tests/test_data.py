"""Regression tests for partial yfinance failures (issue #102)."""
import numpy as np
import pandas as pd

import engine.data as data


def _fake_download(df):
    class _YF:
        @staticmethod
        def download(tickers, **kwargs):
            return {"Close": df}
    return _YF


def test_all_nan_column_falls_back_to_cache(monkeypatch):
    idx = pd.bdate_range("2024-01-02", periods=5)
    df = pd.DataFrame({
        "NVDA": [100.0 + i for i in range(5)],
        "MSFT": [np.nan] * 5,
    }, index=idx)
    monkeypatch.setattr(data.yf, "download", _fake_download(df).download)

    out = data.load_prices(["NVDA", "MSFT"])
    # Falls back to data/prices.csv: both columns populated, no all-NaN col.
    assert not out.empty
    assert out["NVDA"].notna().any() and out["MSFT"].notna().any()
    assert not out.isna().all().any()


def test_missing_ticker_column_falls_back_to_cache(monkeypatch):
    idx = pd.bdate_range("2024-01-02", periods=5)
    df = pd.DataFrame({"NVDA": [100.0 + i for i in range(5)]}, index=idx)
    monkeypatch.setattr(data.yf, "download", _fake_download(df).download)

    out = data.load_prices(["NVDA", "MSFT"])
    assert "MSFT" in out.columns and out["MSFT"].notna().any()


def test_clean_download_returned_directly(monkeypatch):
    idx = pd.bdate_range("2024-01-02", periods=5)
    df = pd.DataFrame({
        "NVDA": [100.0 + i for i in range(5)],
        "MSFT": [200.0 + i for i in range(5)],
    }, index=idx)
    monkeypatch.setattr(data.yf, "download", _fake_download(df).download)

    out = data.load_prices(["NVDA", "MSFT"])
    assert len(out) == 5 and list(out.columns) == ["NVDA", "MSFT"]
