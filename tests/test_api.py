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
    # Series alignment checks (#175)
    assert len(data["dates"]) == len(data["price_series"]["Portfolio"])
    assert len(data["dates"]) == len(data["drawdown_series"])
    assert data["price_series"]["Portfolio"][0] == 100.0
    assert data["drawdown_series"][0] == 0.0

def test_risk_history_series_alignment_175():
    from unittest.mock import patch
    import pandas as pd
    dates = pd.bdate_range("2026-10-05", periods=26)
    prices = pd.DataFrame({
        "NVDA": [100, 110, 88] + [88] * 23,
        "MSFT": [100] * 3 + [100 + day / 10 for day in range(1, 24)],
    }, index=dates)
    with patch("api.load_prices", return_value=prices):
        result = client.post("/risk", json={"weights": {"NVDA": 50, "MSFT": 50}}).json()
    assert len(result["dates"]) == 26
    assert len(result["price_series"]["Portfolio"]) == 26
    assert len(result["drawdown_series"]) == 26
    assert result["price_series"]["Portfolio"][0] == 100.0
    assert result["drawdown_series"][0] == 0.0
    assert result["price_series"]["Portfolio"][1] == 105.0
    assert result["drawdown_series"][1] == 0.0
    assert result["price_series"]["Portfolio"][2] == 94.5
    assert result["drawdown_series"][2] == -0.1

def test_risk_history_missing_quote_handling_175():
    from unittest.mock import patch
    import pandas as pd
    import numpy as np
    dates = pd.bdate_range("2026-10-05", periods=26)
    prices = pd.DataFrame({
        "NVDA": [100, 110, 88] + [88] * 23,
        "MSFT": [100, np.nan, 100] + [100 + day / 10 for day in range(1, 24)],
    }, index=dates)
    with patch("api.load_prices", return_value=prices):
        result = client.post("/risk", json={"weights": {"NVDA": 50, "MSFT": 50}}).json()
    assert len(result["dates"]) == 26
    assert len(result["price_series"]["Portfolio"]) == 26
    assert result["price_series"]["Portfolio"][0] == 100.0
    assert result["price_series"]["Portfolio"][1] is None
    assert result["drawdown_series"][1] is None

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
