import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from api import _normalize_and_validate_weights, app

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

def test_risk_duplicate_canonical_ticker():
    # Duplicate canonical ticker with case variance
    response = client.post("/risk", json={"weights": {"AAPL": 40, "aapl": 60, "MSFT": 50}})
    assert response.status_code == 400
    assert "Duplicate canonical ticker: AAPL" in response.json()["detail"]

    # Duplicate canonical ticker with whitespace variance
    response_ws = client.post("/risk", json={"weights": {"AAPL": 40, " AAPL ": 60, "MSFT": 50}})
    assert response_ws.status_code == 400
    assert "Duplicate canonical ticker: AAPL" in response_ws.json()["detail"]

def test_liquidity_duplicate_canonical_ticker():
    response = client.post("/liquidity", json={
        "portfolio_value": 100000,
        "weights": {"AAPL": 40, "aapl": 60, "MSFT": 50},
        "adv_participation": 0.1
    })
    assert response.status_code == 400
    assert "Duplicate canonical ticker: AAPL" in response.json()["detail"]

def test_normalize_and_validate_weights_canonical_controls():
    # Canonical tickers
    res = _normalize_and_validate_weights({"AAPL": 40, "MSFT": 60})
    assert res["AAPL"] == pytest.approx(0.4)
    assert res["MSFT"] == pytest.approx(0.6)

    # Unique alias tickers (normalized to uppercase)
    res_alias = _normalize_and_validate_weights({"aapl": 40, "msft": 60})
    assert "AAPL" in res_alias
    assert "MSFT" in res_alias
    assert res_alias["AAPL"] == pytest.approx(0.4)
    assert res_alias["MSFT"] == pytest.approx(0.6)

    # Unique whitespace tickers
    res_ws = _normalize_and_validate_weights({"  aapl  ": 40, " msft ": 60})
    assert res_ws["AAPL"] == pytest.approx(0.4)
    assert res_ws["MSFT"] == pytest.approx(0.6)

def test_normalize_and_validate_weights_duplicate_rejection():
    # Case collision
    with pytest.raises(HTTPException) as exc_info:
        _normalize_and_validate_weights({"AAPL": 40, "aapl": 60, "MSFT": 50})
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Duplicate canonical ticker: AAPL"

    # Reversed case collision
    with pytest.raises(HTTPException) as exc_info:
        _normalize_and_validate_weights({"aapl": 60, "AAPL": 40, "MSFT": 50})
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Duplicate canonical ticker: AAPL"

    # Whitespace collision
    with pytest.raises(HTTPException) as exc_info:
        _normalize_and_validate_weights({"AAPL": 40, " AAPL ": 60, "MSFT": 50})
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Duplicate canonical ticker: AAPL"

    # Overwritten negative collision
    with pytest.raises(HTTPException) as exc_info:
        _normalize_and_validate_weights({"aapl": -40, "AAPL": 100, "MSFT": 50})
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Duplicate canonical ticker: AAPL"

def test_normalize_and_validate_weights_negative_and_empty():
    # Negative weight without duplicate
    with pytest.raises(HTTPException) as exc_info:
        _normalize_and_validate_weights({"aapl": -40, "MSFT": 50})
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Weights must be positive numbers summing to > 0"

    # Empty dictionary
    with pytest.raises(HTTPException) as exc_info:
        _normalize_and_validate_weights({})
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Portfolio weights cannot be empty"

    # Unknown ticker
    with pytest.raises(HTTPException) as exc_info:
        _normalize_and_validate_weights({"UNKNOWN_TICKER": 100})
    assert exc_info.value.status_code == 400
    assert "Unsupported tickers" in exc_info.value.detail

