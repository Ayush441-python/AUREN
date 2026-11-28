import pandas as pd
import pytest
from fastapi.testclient import TestClient

import api as api_module
import engine.data as data_module
from api import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clear_data_memo():
    with data_module._lock:
        data_module._memo.clear()


def test_usdc_does_not_hit_yfinance_otc_stock(monkeypatch):
    """Raw 'USDC' must resolve to a $1.00 peg rather than calling yfinance (where 'USDC'
    collides with OTC penny stock US Data Corp at 780.92% volatility)."""
    called_tickers: list[list[str]] = []

    def fake_download(field: str, tickers: list[str], period: str):
        called_tickers.append(list(tickers))
        return None  # simulate offline / fallback to bundled CSV cache

    monkeypatch.setattr(data_module, "_download", fake_download)

    res = client.post("/risk", json={"weights": {"USDC": 100}})
    assert res.status_code == 200
    data = res.json()
    assert called_tickers == []
    assert data["volatility"] == pytest.approx(0.0)
    assert data["max_drawdown"] == pytest.approx(0.0)
    assert not any("Volatility" in r for r in data["reasons"])
    assert all(p == pytest.approx(100.0) for p in data["price_series"]["USDC"])


def test_preset_macro_defensive_with_usdc_reduces_volatility_proportionally(monkeypatch):
    """Adding 10% USDC cash to a cached equity portfolio (or Preset 4) must scale
    volatility down proportionally (~0.90x) and never pass 'USDC' to _download."""
    called: list[list[str]] = []

    def offline_download(field: str, tickers: list[str], period: str):
        called.append(list(tickers))
        return None

    monkeypatch.setattr(data_module, "_download", offline_download)

    res_no_cash = client.post("/risk", json={"weights": {"AAPL": 45, "MSFT": 45}})
    res_with_usdc = client.post(
        "/risk", json={"weights": {"AAPL": 45, "MSFT": 45, "USDC": 10}}
    )
    assert res_no_cash.status_code == 200
    assert res_with_usdc.status_code == 200
    assert all("USDC" not in batch for batch in called)

    vol_no_cash = res_no_cash.json()["volatility"]
    vol_with_usdc = res_with_usdc.json()["volatility"]
    assert vol_with_usdc == pytest.approx(vol_no_cash * 0.90, rel=1e-2)
    assert res_with_usdc.json()["max_drawdown"] > res_no_cash.json()["max_drawdown"]


def test_liquidity_with_usdc_succeeds_offline_and_calculates_instant_exit(monkeypatch):
    monkeypatch.setattr(data_module, "_download", lambda field, tickers, period: None)

    res = client.post(
        "/liquidity",
        json={"portfolio_value": 100000, "weights": {"NVDA": 50, "USDC": 50}},
    )
    assert res.status_code == 200
    assets = {a["ticker"]: a for a in res.json()["assets"]}
    assert "USDC" in assets
    assert assets["USDC"]["adv"] == pytest.approx(5_000_000_000.0)
    assert assets["USDC"]["days_to_exit"] < 0.001
