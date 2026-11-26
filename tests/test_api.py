from fastapi.testclient import TestClient
from backend.app.main import app

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
    import backend.app.main as api_module

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
    import backend.app.main as api_module

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


def test_liquidity_exit_days_precision_preserves_over_cap_boundary(monkeypatch):
    """Verify days_to_exit preserves calculated float precision across capacity boundaries."""
    import numpy as np
    import pandas as pd
    import pytest
    import backend.app.main as api_module

    prices = pd.DataFrame({"MSFT": [100.0] * 30, "AAPL": [100.0] * 30})
    volumes = pd.DataFrame({"MSFT": [100_000] * 30, "AAPL": [100_000] * 30})
    monkeypatch.setattr(api_module, "load_prices", lambda tickers, period="2y": prices[list(tickers)])
    monkeypatch.setattr(api_module, "load_volumes", lambda tickers, period="2y": volumes[list(tickers)])

    for w in ({"MSFT": 499, "AAPL": 501}, {"MSFT": 49999, "AAPL": 50001}, {"AAPL": 50001, "MSFT": 49999}, {"MSFT": 4_999_999, "AAPL": 5_000_001}):
        res = client.post("/liquidity", json={"portfolio_value": 2_000_000, "weights": w, "adv_participation": 0.1})
        assert res.status_code == 200
        d = res.json()
        by_t = {a["ticker"]: a["days_to_exit"] for a in d["assets"]}
        assert by_t["MSFT"] < 1.0 < by_t["AAPL"]
        assert d["max_days_to_exit"] == by_t["AAPL"] > 1.0

    # Exact 1.0 tie & missing NaN volume fallback
    res_eq = client.post("/liquidity", json={"portfolio_value": 2_000_000, "weights": {"MSFT": 50, "AAPL": 50}, "adv_participation": 0.1}).json()
    assert res_eq["max_days_to_exit"] == pytest.approx(1.0)

    volumes_nan = pd.DataFrame({"MSFT": [np.nan] * 30, "AAPL": [np.nan] * 30})
    monkeypatch.setattr(api_module, "load_volumes", lambda tickers, period="2y": volumes_nan[list(tickers)])
    res_nan = client.post("/liquidity", json={"portfolio_value": 100_000, "weights": {"MSFT": 50, "AAPL": 50}, "adv_participation": 0.1}).json()
    assert all(a["days_to_exit"] is None for a in res_nan["assets"])
    assert res_nan["max_days_to_exit"] == 0.0
