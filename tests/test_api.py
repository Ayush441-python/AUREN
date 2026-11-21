import pytest
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


@pytest.mark.parametrize("body", [
    '{"weights":{"NVDA":NaN,"MSFT":50}}',
    '{"weights":{"NVDA":Infinity,"MSFT":50}}',
    '{"weights":{"NVDA":-Infinity,"MSFT":50}}',
])
def test_risk_non_finite_weights_rejected(body):
    # Python's json.loads accepts NaN/Infinity literals; they must not reach metrics.
    response = client.post("/risk", content=body,
                           headers={"content-type": "application/json"})
    assert response.status_code == 400
    assert "finite" in response.json()["detail"]

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
