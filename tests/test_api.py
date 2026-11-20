import math
import pandas as pd
from unittest.mock import patch
from starlette.testclient import TestClient
import engine.data as data_mod
from api import app

client = TestClient(app, raise_server_exceptions=True)


def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "AUREN Risk API"


def test_risk_valid_portfolio():
    resp = client.post("/risk", json={"weights": {"NVDA": 40, "MSFT": 30, "GOOGL": 20, "ETH-USD": 10}})
    assert resp.status_code == 200
    data = resp.json()
    assert "score" in data
    assert "level" in data
    assert "volatility" in data and not math.isnan(data["volatility"])
    assert "max_drawdown" in data and not math.isnan(data["max_drawdown"])
    assert "concentration" in data
    assert "sector_exposure" in data
    assert "correlated_pairs" in data
    assert "stress" in data


def test_risk_empty_weights_400():
    resp = client.post("/risk", json={"weights": {}})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Portfolio weights cannot be empty"


def test_risk_unsupported_tickers_400():
    resp = client.post("/risk", json={"weights": {"UNKNOWN_TICKER": 100}})
    assert resp.status_code == 400
    assert "Unsupported tickers" in resp.json()["detail"]


def test_risk_invalid_weights_400():
    resp = client.post("/risk", json={"weights": {"NVDA": -10, "MSFT": 20}})
    assert resp.status_code == 400
    assert "Weights must be positive numbers" in resp.json()["detail"]

    resp = client.post("/risk", json={"weights": {"NVDA": 0, "MSFT": 0}})
    assert resp.status_code == 400
    assert "Weights must be positive numbers" in resp.json()["detail"]


def test_risk_yfinance_throttled_falls_back_to_cache_200():
    # Issue #102: when yfinance throttles MSFT, it should fallback to cache and return 200
    dates = pd.date_range("2026-01-01", periods=10, freq="D")
    partial = pd.DataFrame({"NVDA": [100.0 + i for i in range(10)], "MSFT": [float("nan")] * 10}, index=dates)
    with patch.object(data_mod.yf, "download", return_value={"Close": partial}):
        resp = client.post("/risk", json={"weights": {"NVDA": 50, "MSFT": 50}})
        assert resp.status_code == 200
        data = resp.json()
        assert not math.isnan(data["volatility"])
        assert not math.isnan(data["max_drawdown"])


def test_risk_empty_prices_500():
    with patch("api.load_prices", return_value=pd.DataFrame()):
        resp = client.post("/risk", json={"weights": {"NVDA": 50, "MSFT": 50}})
        assert resp.status_code == 500
        assert resp.json()["detail"] == "Failed to load historical price series"


def test_risk_insufficient_prices_less_than_2_rows_500():
    dates = pd.date_range("2026-01-01", periods=1, freq="D")
    one_row = pd.DataFrame({"NVDA": [100.0], "MSFT": [200.0]}, index=dates)
    with patch("api.load_prices", return_value=one_row):
        resp = client.post("/risk", json={"weights": {"NVDA": 50, "MSFT": 50}})
        assert resp.status_code == 500
        assert resp.json()["detail"] == "Failed to load historical price series"


def test_risk_missing_ticker_in_prices_500():
    dates = pd.date_range("2026-01-01", periods=10, freq="D")
    missing_col = pd.DataFrame({"NVDA": [100.0] * 10}, index=dates)
    with patch("api.load_prices", return_value=missing_col):
        resp = client.post("/risk", json={"weights": {"NVDA": 50, "MSFT": 50}})
        assert resp.status_code == 500
        assert resp.json()["detail"] == "Failed to load historical price series"


def test_risk_disjoint_dates_prices_500():
    dates = pd.date_range("2026-01-01", periods=2, freq="D")
    disjoint = pd.DataFrame({
        "NVDA": [100.0, float("nan")],
        "MSFT": [float("nan"), 200.0]
    }, index=dates)
    with patch("api.load_prices", return_value=disjoint):
        resp = client.post("/risk", json={"weights": {"NVDA": 50, "MSFT": 50}})
        assert resp.status_code == 500
        assert resp.json()["detail"] == "Failed to load historical price series"
