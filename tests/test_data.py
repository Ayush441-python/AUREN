import random

import pandas as pd
import pytest

import engine.data as data


@pytest.fixture
def fake_download(monkeypatch):
    """Empty memo cache and a stubbed Yahoo download that records each call."""
    monkeypatch.setattr(data, "_memo", {})
    calls = []

    def _fake(field, tickers, period):
        calls.append((field, list(tickers)))
        idx = pd.date_range("2025-01-01", periods=3, freq="D")
        # Like Yahoo, return the columns sorted, not in request order.
        return pd.DataFrame({t: [1.0, 2.0, 3.0] for t in sorted(tickers)}, index=idx)

    monkeypatch.setattr(data, "_download", _fake)
    return calls


@pytest.mark.parametrize("loader", [data.load_prices, data.load_volumes])
def test_warm_cache_keeps_current_request_column_order(fake_download, loader):
    first = loader(["AAPL", "MSFT", "NVDA"])
    second = loader(["NVDA", "MSFT", "AAPL"])

    assert first.columns.tolist() == ["AAPL", "MSFT", "NVDA"]
    assert second.columns.tolist() == ["NVDA", "MSFT", "AAPL"]
    assert len(fake_download) == 1  # second call was served from the memo cache


POOL = [f"T{i:02d}" for i in range(20)]


@pytest.mark.parametrize("loader", [data.load_prices, data.load_volumes])
@pytest.mark.parametrize("seed", range(49))
def test_warm_cache_order_randomized(monkeypatch, loader, seed):
    """Random ticker sets, orders, duplicates and tickers Yahoo skips."""
    rng = random.Random(seed)
    universe = rng.sample(POOL, rng.randint(2, 8))
    # At least two tickers have data, so there is an order to get wrong.
    unavailable = set(rng.sample(universe, rng.randint(0, len(universe) - 2)))
    calls = []

    def _fake(field, tickers, period):
        calls.append(list(tickers))
        idx = pd.date_range("2025-01-01", periods=3, freq="D")
        # Sorted like Yahoo; each ticker gets distinct values so a swapped column is caught.
        cols = {t: [POOL.index(t) * 10.0 + r for r in range(3)]
                for t in sorted(tickers) if t not in unavailable}
        return pd.DataFrame(cols, index=idx)

    monkeypatch.setattr(data, "_memo", {})
    monkeypatch.setattr(data, "_download", _fake)
    monkeypatch.setattr(data, "_cached", lambda path, tickers: pd.DataFrame())

    first = rng.sample(universe, len(universe))
    available_first = [t for t in first if t not in unavailable]
    while True:
        second = rng.sample(universe, len(universe))
        second += rng.choices(universe, k=rng.randint(0, 3))  # duplicates
        rng.shuffle(second)
        expected = [t for t in dict.fromkeys(second) if t not in unavailable]
        if expected != available_first:  # the second request must reorder the data
            break

    loader(first)
    result = loader(second)

    assert result.columns.tolist() == expected
    for t in expected:
        assert result[t].tolist() == [POOL.index(t) * 10.0 + r for r in range(3)]
    assert len(calls) == 1  # second call was served from the memo cache
