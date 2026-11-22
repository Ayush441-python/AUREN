from fastapi.testclient import TestClient
from api import app

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


def test_concentration_30pct_rule_boundary_agreement(monkeypatch):
    import api as api_module
    import pandas as pd

    tickers = ["NVDA", "COST", "MSFT", "XOM"]
    prices = pd.DataFrame(
        {ticker: range(100 + i, 130 + i) for i, ticker in enumerate(tickers)},
        index=pd.bdate_range("2026-01-02", periods=30),
    )
    monkeypatch.setattr(api_module, "_load_aligned_prices", lambda *args, **kwargs: prices)

    # 1. Exact 30% boundary must remain unflagged (no 20-point penalty, exceeds_30pct=False)
    w_30 = dict(zip(tickers, [30.0, 24.0, 23.0, 23.0]))
    res_30 = api_module.compute_risk(api_module.PortfolioRequest(weights=w_30))
    hit_30 = any(n == 20 and why.startswith("Largest holding") for n, why in res_30["hits"])
    assert hit_30 is False
    assert res_30["concentration"]["exceeds_30pct"] is False
    assert res_30["concentration"]["top_weight"] == 0.3

    # 2. 30.004% slightly above boundary must flag consistently in both score and concentration
    w_30_004 = dict(zip(tickers, [30.004, 24.0, 23.0, 22.996]))
    res_30_004 = api_module.compute_risk(api_module.PortfolioRequest(weights=w_30_004))
    hit_30_004 = any(n == 20 and why.startswith("Largest holding") for n, why in res_30_004["hits"])
    assert hit_30_004 is True
    assert res_30_004["concentration"]["exceeds_30pct"] is True
    assert res_30_004["concentration"]["top_weight"] == 0.30004

    # 3. 30.01% clearly above boundary must also flag consistently
    w_30_01 = dict(zip(tickers, [30.01, 24.0, 23.0, 22.99]))
    res_30_01 = api_module.compute_risk(api_module.PortfolioRequest(weights=w_30_01))
    hit_30_01 = any(n == 20 and why.startswith("Largest holding") for n, why in res_30_01["hits"])
    assert hit_30_01 is True
    assert res_30_01["concentration"]["exceeds_30pct"] is True
    assert res_30_01["concentration"]["top_weight"] == 0.3001

