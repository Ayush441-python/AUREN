"""Regression tests for issue #195: refresh_cache must not report success
when a market-data download fails and silently falls back to the bundled CSV."""
import hashlib
import runpy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pandas as pd
import pytest

from engine import data

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "refresh_cache.py"


def _run_refresh(prices_csv: str, volumes_csv: str, downloads):
    with TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        prices, volumes = tmp / "prices.csv", tmp / "volume.csv"
        prices.write_text(prices_csv, encoding="utf-8")
        volumes.write_text(volumes_csv, encoding="utf-8")
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in (prices, volumes)}
        data._memo.clear()
        with patch.multiple(data, CACHE=prices, VOL_CACHE=volumes), \
                patch.object(data, "_download", side_effect=downloads):
            with pytest.raises(SystemExit) as exc:
                runpy.run_path(str(SCRIPT), run_name="__main__")
        after = {p: hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in (prices, volumes)}
        return exc.value.code, before == after


def test_volume_download_failure_leaves_cache_untouched():
    prices_csv = "Date,AAPL\n2026-11-18,100\n"
    volumes_csv = "Date,AAPL\n2026-11-18,1000\n"
    fresh_prices = pd.DataFrame({"AAPL": [105]},
                                index=pd.to_datetime(["2026-11-19"]))
    code, untouched = _run_refresh(prices_csv, volumes_csv,
                                   [fresh_prices, None])
    assert code != 0
    assert untouched


def test_both_downloads_failing_leaves_cache_untouched():
    prices_csv = "Date,AAPL\n2026-11-18,100\n"
    volumes_csv = "Date,AAPL\n2026-11-18,1000\n"
    code, untouched = _run_refresh(prices_csv, volumes_csv, [None, None])
    assert code != 0
    assert untouched
