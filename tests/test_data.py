import types
import pandas as pd
from unittest.mock import patch
import engine.data as data_mod
from engine.data import _download, load_prices, load_volumes


def test_download_empty_tickers():
    assert _download("Close", [], "2y") is None


def test_download_valid_dataframe():
    dates = pd.date_range("2026-01-01", periods=5, freq="D")
    df = pd.DataFrame({"NVDA": [10.0, 11.0, 12.0, 13.0, 14.0], "MSFT": [20.0, 21.0, 22.0, 23.0, 24.0]}, index=dates)
    with patch.object(data_mod.yf, "download", return_value={"Close": df}):
        res = _download("Close", ["NVDA", "MSFT"], "2y")
        assert res is not None
        assert list(res.columns) == ["NVDA", "MSFT"]
        assert len(res) == 5


def test_download_series_to_frame():
    dates = pd.date_range("2026-01-01", periods=3, freq="D")
    s = pd.Series([100.0, 101.0, 102.0], index=dates, name="Close")
    with patch.object(data_mod.yf, "download", return_value={"Close": s}):
        res = _download("Close", ["NVDA"], "2y")
        assert res is not None
        assert isinstance(res, pd.DataFrame)
        assert list(res.columns) == ["NVDA"]
        assert len(res) == 3


def test_download_missing_column():
    dates = pd.date_range("2026-01-01", periods=5, freq="D")
    df = pd.DataFrame({"NVDA": [10.0] * 5}, index=dates)
    with patch.object(data_mod.yf, "download", return_value={"Close": df}):
        res = _download("Close", ["NVDA", "MSFT"], "2y")
        assert res is None


def test_download_all_nan_column_returns_none():
    dates = pd.date_range("2026-01-01", periods=5, freq="D")
    df = pd.DataFrame({"NVDA": [10.0] * 5, "MSFT": [float("nan")] * 5}, index=dates)
    with patch.object(data_mod.yf, "download", return_value={"Close": df}):
        res = _download("Close", ["NVDA", "MSFT"], "2y")
        assert res is None


def test_download_no_overlapping_valid_rows_returns_none():
    dates = pd.date_range("2026-01-01", periods=4, freq="D")
    df = pd.DataFrame({
        "NVDA": [10.0, 11.0, float("nan"), float("nan")],
        "MSFT": [float("nan"), float("nan"), 20.0, 21.0]
    }, index=dates)
    with patch.object(data_mod.yf, "download", return_value={"Close": df}):
        res = _download("Close", ["NVDA", "MSFT"], "2y")
        assert res is None


def test_download_exception_returns_none():
    with patch.object(data_mod.yf, "download", side_effect=Exception("Network error")):
        res = _download("Close", ["NVDA"], "2y")
        assert res is None


def test_load_prices_fallback_to_cache_when_throttled():
    dates = pd.date_range("2026-01-01", periods=10, freq="D")
    partial = pd.DataFrame({"NVDA": [100.0 + i for i in range(10)], "MSFT": [float("nan")] * 10}, index=dates)
    with patch.object(data_mod.yf, "download", return_value={"Close": partial}):
        prices = load_prices(["NVDA", "MSFT"])
        assert not prices.empty
        assert "NVDA" in prices.columns and "MSFT" in prices.columns
        assert not prices["MSFT"].isna().all()
        assert not prices["NVDA"].isna().all()


def test_load_volumes_fallback_to_cache_when_throttled():
    dates = pd.date_range("2026-01-01", periods=10, freq="D")
    partial = pd.DataFrame({"NVDA": [1000.0] * 10, "MSFT": [float("nan")] * 10}, index=dates)
    with patch.object(data_mod.yf, "download", return_value={"Volume": partial}):
        vols = load_volumes(["NVDA", "MSFT"])
        assert not vols.empty
        assert "NVDA" in vols.columns and "MSFT" in vols.columns
        assert not vols["MSFT"].isna().all()
