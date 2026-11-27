from pathlib import Path

import pandas as pd

from engine import data


def test_load_empty_cache_returns_empty_frame_without_overwriting(tmp_path, monkeypatch):
    cache = Path(tmp_path) / "prices.csv"
    cache.write_bytes(b"")
    original = cache.read_bytes()
    data._memo.clear()
    monkeypatch.setattr(data, "_download", lambda field, tickers, period: None)

    result = data._load("Close", ["NVDA"], "2y", cache)

    assert result.empty
    assert cache.read_bytes() == original
