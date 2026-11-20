import errno
import runpy
from pathlib import Path

import pandas as pd
import pytest

from engine import data


class InterruptedFrame:
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


@pytest.mark.parametrize("filename, loader", [
    ("prices.csv", "load_prices"),
    ("volume.csv", "load_volumes"),
])
def test_failed_refresh_preserves_previous_cache(monkeypatch, cache_dir, filename, loader):
    path = cache_dir / filename
    previous = path.read_bytes()
    frame = pd.DataFrame({"MSFT": [200]})
    monkeypatch.setattr(data, "load_prices", lambda tickers: frame)
    monkeypatch.setattr(data, "load_volumes", lambda tickers: frame)
    monkeypatch.setattr(data, loader, lambda tickers: InterruptedFrame())

    with pytest.raises(OSError) as error:
        runpy.run_module("scripts.refresh_cache", run_name="__main__")

    assert error.value.errno == errno.ENOSPC
    assert path.read_bytes() == previous
    assert {entry.name for entry in cache_dir.iterdir()} == {"prices.csv", "volume.csv"}


def test_refresh_replaces_both_caches(monkeypatch, cache_dir):
    index = pd.DatetimeIndex(["2026-01-06"], name="Date")
    prices = pd.DataFrame({"MSFT": [200.5]}, index=index)
    volumes = pd.DataFrame({"MSFT": [500]}, index=index)
    monkeypatch.setattr(data, "load_prices", lambda tickers: prices)
    monkeypatch.setattr(data, "load_volumes", lambda tickers: volumes)

    runpy.run_module("scripts.refresh_cache", run_name="__main__")

    for filename, expected in (("prices.csv", prices), ("volume.csv", volumes)):
        actual = pd.read_csv(cache_dir / filename, index_col=0, parse_dates=True)
        pd.testing.assert_frame_equal(actual, expected)
    assert {entry.name for entry in cache_dir.iterdir()} == {"prices.csv", "volume.csv"}
