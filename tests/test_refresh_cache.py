import pathlib
import runpy
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pandas as pd
import pytest

from engine import data
from engine.data import load_prices, load_volumes


@pytest.fixture(autouse=True)
def clear_engine_memo():
    with data._lock:
        data._memo.clear()
    yield
    with data._lock:
        data._memo.clear()


def test_require_download_behavior():
    """Verify require_download=True returns empty DataFrame on failure, while default falls back to cache."""
    with TemporaryDirectory() as tmp:
        cache_file = pathlib.Path(tmp) / "prices.csv"
        cache_file.write_text("Date,AAPL\n2026-11-18,100\n", encoding="utf-8")

        with patch.object(data, "CACHE", cache_file), patch.object(data, "_download", return_value=None):
            # require_download=False should fallback to bundled CSV
            df_fallback = load_prices(["AAPL"], require_download=False)
            assert not df_fallback.empty
            assert df_fallback.iloc[0]["AAPL"] == 100

            # require_download=True should return empty DataFrame immediately
            df_strict = load_prices(["AAPL"], require_download=True)
            assert df_strict.empty


def test_refresh_cache_aborts_when_volume_fails():
    """If prices succeed but volume download fails, refresh_cache must abort without modifying files."""
    with TemporaryDirectory() as tmp:
        prices_csv = pathlib.Path(tmp) / "prices.csv"
        volumes_csv = pathlib.Path(tmp) / "volume.csv"
        initial_prices = "Date,AAPL\n2026-11-18,100\n"
        initial_volumes = "Date,AAPL\n2026-11-18,1000\n"
        prices_csv.write_text(initial_prices, encoding="utf-8")
        volumes_csv.write_text(initial_volumes, encoding="utf-8")

        fresh_prices = pd.DataFrame({"AAPL": [105.0]}, index=pd.to_datetime(["2026-11-19"]))

        with patch.multiple(data, CACHE=prices_csv, VOL_CACHE=volumes_csv), patch.object(
            data, "_download", side_effect=[fresh_prices, None]
        ):
            with pytest.raises(SystemExit) as exc_info:
                runpy.run_path("scripts/refresh_cache.py", run_name="__main__")

            assert "Download failed" in str(exc_info.value) or "Refusing to write partial cache" in str(exc_info.value)

        # Confirm original cache files are completely untouched
        assert prices_csv.read_text(encoding="utf-8") == initial_prices
        assert volumes_csv.read_text(encoding="utf-8") == initial_volumes


def test_refresh_cache_aborts_when_dates_mismatched():
    """If prices and volumes end on different dates, refresh_cache refuses to write partial cache."""
    with TemporaryDirectory() as tmp:
        prices_csv = pathlib.Path(tmp) / "prices.csv"
        volumes_csv = pathlib.Path(tmp) / "volume.csv"
        initial_prices = "Date,AAPL\n2026-11-18,100\n"
        initial_volumes = "Date,AAPL\n2026-11-18,1000\n"
        prices_csv.write_text(initial_prices, encoding="utf-8")
        volumes_csv.write_text(initial_volumes, encoding="utf-8")

        fresh_prices = pd.DataFrame({"AAPL": [105.0]}, index=pd.to_datetime(["2026-11-20"]))
        fresh_volumes = pd.DataFrame({"AAPL": [1200.0]}, index=pd.to_datetime(["2026-11-19"]))

        with patch.multiple(data, CACHE=prices_csv, VOL_CACHE=volumes_csv), patch.object(
            data, "_download", side_effect=[fresh_prices, fresh_volumes]
        ):
            with pytest.raises(SystemExit) as exc_info:
                runpy.run_path("scripts/refresh_cache.py", run_name="__main__")

            assert "Refusing to write partial cache" in str(exc_info.value)

        assert prices_csv.read_text(encoding="utf-8") == initial_prices
        assert volumes_csv.read_text(encoding="utf-8") == initial_volumes


def test_refresh_cache_happy_path(capsys):
    """When both downloads succeed with aligned dates, refresh_cache commits new data."""
    with TemporaryDirectory() as tmp:
        prices_csv = pathlib.Path(tmp) / "prices.csv"
        volumes_csv = pathlib.Path(tmp) / "volume.csv"
        prices_csv.write_text("Date,AAPL\n2026-11-18,100\n", encoding="utf-8")
        volumes_csv.write_text("Date,AAPL\n2026-11-18,1000\n", encoding="utf-8")

        fresh_prices = pd.DataFrame({"AAPL": [105.0]}, index=pd.to_datetime(["2026-11-19"]))
        fresh_volumes = pd.DataFrame({"AAPL": [1500.0]}, index=pd.to_datetime(["2026-11-19"]))

        with patch.multiple(data, CACHE=prices_csv, VOL_CACHE=volumes_csv), patch.object(
            data, "_download", side_effect=[fresh_prices, fresh_volumes]
        ):
            runpy.run_path("scripts/refresh_cache.py", run_name="__main__")

        assert "2026-11-19" in prices_csv.read_text(encoding="utf-8")
        assert "2026-11-19" in volumes_csv.read_text(encoding="utf-8")
        captured = capsys.readouterr()
        assert "Saved" in captured.out
