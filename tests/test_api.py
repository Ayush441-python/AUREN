import json
from unittest.mock import patch
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from api import app


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


def test_api_root(client):
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "AUREN Risk API"


def test_api_risk_empty_weights(client):
    res = client.post("/risk", json={"weights": {}})
    assert res.status_code == 400
    assert "Portfolio weights cannot be empty" in res.json()["detail"]


def test_api_risk_unsupported_tickers(client):
    res = client.post("/risk", json={"weights": {"NON_EXISTENT_TICKER": 100}})
    assert res.status_code == 400
    assert "Unsupported tickers:" in res.json()["detail"]


def test_api_risk_invalid_weights(client):
    res = client.post("/risk", json={"weights": {"NVDA": -10, "MSFT": 20}})
    assert res.status_code == 400
    assert "Weights must be positive" in res.json()["detail"]


def test_api_risk_missing_price_series_returns_400(client):
    # User submits portfolio with tickers ["NVDA", "ETH-USD"], but cached price table only contains "NVDA"
    with patch("api.load_prices") as mock_lp:
        mock_lp.return_value = pd.DataFrame({"NVDA": [120.0, 122.0, 121.0]})
        res = client.post("/risk", json={"weights": {"NVDA": 60, "ETH-USD": 40}})
        assert res.status_code == 400
        detail = res.json()["detail"]
        assert "Historical price series unavailable for:" in detail
        assert "ETH-USD" in detail


def test_api_risk_all_prices_unavailable_returns_400(client):
    with patch("api.load_prices") as mock_lp:
        mock_lp.return_value = pd.DataFrame()
        res = client.post("/risk", json={"weights": {"NVDA": 100}})
        assert res.status_code == 400
        detail = res.json()["detail"]
        assert "Historical price series unavailable for:" in detail
        assert "NVDA" in detail


def test_api_risk_rfc8259_json_compliance_single_observation(client):
    # Single observation would previously produce NaN volatility and max_drawdown
    with patch("api.load_prices") as mock_lp:
        mock_lp.return_value = pd.DataFrame({"NVDA": [120.0]})
        res = client.post("/risk", json={"weights": {"NVDA": 100}})
        assert res.status_code == 200

        # Strict RFC 8259 compliance verification:
        # Standard Python json.loads with allow_nan=False must succeed without ValueError
        body_text = res.text
        assert "NaN" not in body_text
        assert "Infinity" not in body_text
        assert "-Infinity" not in body_text

        data = json.loads(body_text)
        assert data["volatility"] == 0.0
        assert data["max_drawdown"] == 0.0
        assert isinstance(data["score"], int)


def test_api_risk_valid_portfolio(client):
    res = client.post(
        "/risk",
        json={"weights": {"NVDA": 40, "MSFT": 30, "GOOGL": 20, "ETH-USD": 10}},
    )
    assert res.status_code == 200

    body_text = res.text
    assert "NaN" not in body_text
    assert "Infinity" not in body_text

    data = json.loads(body_text)
    assert "score" in data
    assert "level" in data
    assert "reasons" in data
    assert "concentration" in data
    assert "volatility" in data
    assert "max_drawdown" in data
    assert "sector_exposure" in data
    assert "correlated_pairs" in data
    assert "stress" in data
