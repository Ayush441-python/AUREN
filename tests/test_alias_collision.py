import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from api import app, _normalize_and_validate_weights

client = TestClient(app)


def test_case_insensitive_duplicate_ticker_rejected():
    with pytest.raises(HTTPException) as exc_info:
        _normalize_and_validate_weights({"AAPL": 40, "aapl": 60, "MSFT": 50})
    assert exc_info.value.status_code == 400
    assert "Duplicate canonical ticker: 'AAPL'" in exc_info.value.detail


def test_whitespace_duplicate_ticker_rejected():
    with pytest.raises(HTTPException) as exc_info:
        _normalize_and_validate_weights({"AAPL": 40, "  AAPL  ": 60, "MSFT": 50})
    assert exc_info.value.status_code == 400
    assert "Duplicate canonical ticker: 'AAPL'" in exc_info.value.detail


def test_negative_weight_with_alias_cannot_bypass_validation():
    # Attempting to bypass negative weight check via duplicate casing
    with pytest.raises(HTTPException) as exc_info:
        _normalize_and_validate_weights({"aapl": -40, "AAPL": 100, "MSFT": 50})
    assert exc_info.value.status_code == 400
    assert "Duplicate canonical ticker: 'AAPL'" in exc_info.value.detail


def test_crypto_aliasing_collision_rejected():
    # "ETH" aliases to "ETH-USD", colliding with explicit "ETH-USD"
    with pytest.raises(HTTPException) as exc_info:
        _normalize_and_validate_weights({"ETH": 50, "ETH-USD": 50})
    assert exc_info.value.status_code == 400
    assert "Duplicate canonical ticker: 'ETH-USD'" in exc_info.value.detail


def test_valid_unique_tickers_succeed():
    # Valid diverse tickers normalize properly without false positives
    w = _normalize_and_validate_weights({"AAPL": 50, "MSFT": 50})
    assert w["AAPL"] == pytest.approx(0.5)
    assert w["MSFT"] == pytest.approx(0.5)

    # Valid lowercase crypto tickers aliasing properly
    w_crypto = _normalize_and_validate_weights({"eth": 40, "btc": 60})
    assert w_crypto["ETH-USD"] == pytest.approx(0.4)
    assert w_crypto["BTC-USD"] == pytest.approx(0.6)


def test_api_risk_endpoint_rejects_duplicate_canonical_tickers():
    response = client.post(
        "/risk",
        json={"weights": {"NVDA": 40, "nvda": 60}},
    )
    assert response.status_code == 400
    assert "Duplicate canonical ticker: 'NVDA'" in response.json()["detail"]


def test_api_liquidity_endpoint_rejects_duplicate_canonical_tickers():
    response = client.post(
        "/liquidity",
        json={"portfolio_value": 100000.0, "weights": {"MSFT": 50, " msft ": 50}},
    )
    assert response.status_code == 400
    assert "Duplicate canonical ticker: 'MSFT'" in response.json()["detail"]
