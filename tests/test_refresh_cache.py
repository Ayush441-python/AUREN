import errno
import runpy
import time
from pathlib import Path

import pandas as pd
import pytest

from engine import data


class InterruptedFrame:
    # Mimic the DataFrame interface used by the refresh guard before to_csv.
    empty = False

    def to_csv(self, destination):
        partial_csv = "Date,MSFT\n2026-01-06,"
        if hasattr(destination, "write"):
            destination.write(partial_csv)
        else:
            Path(destination).write_text(partial_csv, encoding="utf-8")
        raise OSError(errno.ENOSPC, "No space left on device")


@pytest.fixture
def cache_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(data, "_memo", {})
    directory = tmp_path / "data"
    directory.mkdir()
    history = pd.DataFrame(
        {"MSFT": range(100, 130)},
        index=pd.bdate_range(end="2026-01-05", periods=30, name="Date"),
    )
    for constant, filename in (("CACHE", "prices.csv"), ("VOL_CACHE", "volume.csv")):
        path = directory / filename
        history.to_csv(path)
        monkeypatch.setattr(data, constant, path)
    return directory


@pytest.mark.parametrize(
    "filename, loader",
    [
        ("prices.csv", "load_prices"),
        ("volume.csv", "load_volumes"),
    ],
)
def test_failed_refresh_preserves_previous_cache(monkeypatch, cache_dir, filename, loader):
    path = cache_dir / filename
    previous = path.read_bytes()
    frame = pd.DataFrame({"MSFT": [200]})
    monkeypatch.setattr(data, "load_prices", lambda tickers, **kwargs: frame)
    monkeypatch.setattr(data, "load_volumes", lambda tickers, **kwargs: frame)
    monkeypatch.setattr(data, loader, lambda tickers, **kwargs: InterruptedFrame())

    with pytest.raises(OSError) as error:
        runpy.run_module("scripts.refresh_cache", run_name="__main__")

    assert error.value.errno == errno.ENOSPC
    assert path.read_bytes() == previous
    assert {entry.name for entry in cache_dir.iterdir()} == {"prices.csv", "volume.csv"}


def test_refresh_replaces_both_caches(monkeypatch, cache_dir):
    index = pd.DatetimeIndex(["2026-01-06"], name="Date")
    prices = pd.DataFrame({"MSFT": [200.5]}, index=index)
    volumes = pd.DataFrame({"MSFT": [500]}, index=index)
    monkeypatch.setattr(data, "load_prices", lambda tickers, **kwargs: prices)
    monkeypatch.setattr(data, "load_volumes", lambda tickers, **kwargs: volumes)

    runpy.run_module("scripts.refresh_cache", run_name="__main__")

    for filename, expected in (("prices.csv", prices), ("volume.csv", volumes)):
        actual = pd.read_csv(cache_dir / filename, index_col=0, parse_dates=True)
        pd.testing.assert_frame_equal(actual, expected)
    assert {entry.name for entry in cache_dir.iterdir()} == {"prices.csv", "volume.csv"}


@pytest.mark.parametrize("download_result", [None, pd.DataFrame()], ids=["yahoo-error", "empty-data"])
def test_refresh_aborts_without_new_download_and_preserves_both_caches(
    monkeypatch, cache_dir, download_result
):
    prices_path = cache_dir / "prices.csv"
    volumes_path = cache_dir / "volume.csv"
    previous_prices = prices_path.read_bytes()
    previous_volumes = volumes_path.read_bytes()
    fresh_prices = pd.DataFrame(
        {"MSFT": [200]},
        index=pd.DatetimeIndex(["2026-01-06"], name="Date"),
    )

    def download(field, tickers, period):
        return fresh_prices if field == "Close" else download_result

    monkeypatch.setattr(data, "_download", download)

    with pytest.raises(SystemExit, match="Download failed"):
        runpy.run_module("scripts.refresh_cache", run_name="__main__")

    assert prices_path.read_bytes() == previous_prices
    assert volumes_path.read_bytes() == previous_volumes
    assert {entry.name for entry in cache_dir.iterdir()} == {"prices.csv", "volume.csv"}


def test_forced_download_bypasses_memo_and_does_not_backfill_from_csv(monkeypatch, cache_dir):
    old_cache = pd.DataFrame(
        {"MSFT": [100], "AAPL": [50]},
        index=pd.DatetimeIndex(["2026-01-05"], name="Date"),
    )
    old_cache.to_csv(data.CACHE)
    fresh = pd.DataFrame(
        {"MSFT": [200]},
        index=pd.DatetimeIndex(["2026-01-06"], name="Date"),
    )
    tickers = ["MSFT", "AAPL"]
    data._memo[("Close", tuple(sorted(tickers)), "2y")] = (time.time(), old_cache)
    downloads = []

    def download(field, requested_tickers, period):
        downloads.append((field, requested_tickers, period))
        return fresh

    monkeypatch.setattr(data, "_download", download)

    result = data.load_prices(tickers, require_download=True)

    assert len(downloads) == 1
    assert list(result.columns) == ["MSFT"]
    pd.testing.assert_frame_equal(result, fresh)


def test_api_loader_still_uses_csv_fallback_when_download_fails(monkeypatch, cache_dir):
    expected = pd.read_csv(data.CACHE, index_col=0, parse_dates=True)
    monkeypatch.setattr(data, "_download", lambda field, tickers, period: None)

    actual = data.load_prices(["MSFT"])

    pd.testing.assert_frame_equal(actual, expected[["MSFT"]])
