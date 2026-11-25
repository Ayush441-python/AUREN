from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient

from api import PortfolioRequest, app, compute_risk

client = TestClient(app)

def test_root():
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (200, 307)
    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "online"

def test_healthz():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_universe():
    response = client.get("/universe")
    assert response.status_code == 200
    data = response.json()
    assert "NVDA" in data["sectors"]
    assert "supported_tickers" in data
    assert len(data["supported_tickers"]) > 0

def test_rules():
    response = client.get("/rules")
    assert response.status_code == 200
    assert "rules" in response.json()

def test_risk_valid():
    response = client.post("/risk", json={"weights": {"NVDA": 50, "AAPL": 50}})
    assert response.status_code == 200
    data = response.json()
    assert "score" in data
    assert "level" in data
    assert "concentration" in data
    assert "volatility" in data
    assert "sector_exposure" in data
    assert "stress" in data

def test_risk_invalid_ticker():
    response = client.post("/risk", json={"weights": {"INVALID_TICKER_XYZ": 100}})
    assert response.status_code == 400
    assert "Unsupported tickers" in response.json()["detail"]

def test_risk_empty():
    response = client.post("/risk", json={"weights": {}})
    assert response.status_code == 400

def test_liquidity_valid():
    response = client.post("/liquidity", json={
        "portfolio_value": 100000,
        "weights": {"NVDA": 60, "MSFT": 40},
        "adv_participation": 0.1
    })
    assert response.status_code == 200
    data = response.json()
    assert "assets" in data
    assert len(data["assets"]) == 2
    assert "max_days_to_exit" in data

def test_wallet_invalid_address():
    response = client.post("/wallet", json={"address": "invalid_address"})
    assert response.status_code == 400
    assert "Invalid EVM/Base address" in response.json()["detail"]


def test_risk_mixed_stock_and_crypto_is_json_safe_and_aligned(monkeypatch):
    """Stocks skip weekends, crypto does not. The raw frame has NaN rows; the API must
    drop them so the JSON is valid and every chart series matches `dates`."""
    import numpy as np
    import pandas as pd
    import api as api_module

    idx = pd.date_range("2025-01-01", periods=120, freq="D")  # includes weekends
    rng = np.random.default_rng(0)
    frame = pd.DataFrame({
        "NVDA": 100 * (1 + rng.normal(0, 0.01, len(idx))).cumprod(),
        "ETH-USD": 100 * (1 + rng.normal(0, 0.02, len(idx))).cumprod(),
    }, index=idx)
    frame.loc[frame.index.dayofweek >= 5, "NVDA"] = np.nan  # stock closed on weekends

    monkeypatch.setattr(api_module, "load_prices", lambda tickers, period="2y": frame[list(tickers)])

    response = client.post("/risk", json={"weights": {"NVDA": 60, "ETH-USD": 40}})
    assert response.status_code == 200
    data = response.json()
    n = len(data["dates"])
    assert n >= 30
    assert len(data["drawdown_series"]) == n
    for series in data["price_series"].values():
        assert len(series) == n
        assert None not in series


def test_wallet_endpoint_shape(monkeypatch):
    import api as api_module

    rows = [{"token": "NVDAc", "ticker": "NVDA", "address": "0x1", "tokens": 2.0, "shares": 2.0,
             "price": 100.0, "value": 200.0, "supported": True, "nav_updated": None}]
    monkeypatch.setattr(api_module, "wallet_holdings",
                        lambda addr, supported, rpc: {"rows": rows, "n_tokens": 5})
    response = client.post("/wallet", json={"address": "0x" + "a" * 40})
    assert response.status_code == 200
    data = response.json()
    assert data["portfolio"] == {"NVDA": 1.0}
    assert data["holdings"][0]["ticker"] == "NVDA"
    assert data["total_value"] == 200.0


def test_sui_equity_and_crypto_remain_distinct():
    history = pd.DataFrame(
        {"SUI": [100.0] * 31, "SUI-USD": [10.0] * 30 + [6.0]},
        index=pd.bdate_range("2026-09-01", periods=31),
    )
    with patch("api.load_prices", side_effect=lambda tickers, period: history[tickers]) as prices:
        eq = compute_risk(PortfolioRequest(weights={"SUI": 1}))
        assert prices.call_args.args[0] == ["SUI"]
        assert eq["normalized_weights"] == {"SUI": 1.0}
        assert eq["price_series"]["Portfolio"][-1] == 100.0

        mixed = compute_risk(PortfolioRequest(weights={"SUI": 50, "SUI-USD": 50}))
        assert prices.call_args.args[0] == ["SUI", "SUI-USD"]
        assert mixed["normalized_weights"] == {"SUI": 0.5, "SUI-USD": 0.5}
        assert mixed["price_series"]["Portfolio"][-1] == 80.0
        assert mixed["concentration"]["hhi"] == 0.5

        crypto = compute_risk(PortfolioRequest(weights={"SUI-USD": 1}))
        assert prices.call_args.args[0] == ["SUI-USD"]
        assert crypto["normalized_weights"] == {"SUI-USD": 1.0}
        assert crypto["price_series"]["Portfolio"][-1] == 60.0
