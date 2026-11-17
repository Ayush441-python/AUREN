"""AUREN API must reject insufficient or non-finite return histories gracefully."""
import pandas as pd
from fastapi.testclient import TestClient
import api


def _prices(values):
    return pd.DataFrame(
        {"NVDA": values},
        index=pd.date_range("2026-11-11", periods=len(values), freq="D"),
    )


def test_two_prices_return_validation_instead_of_json_serialization_crash(monkeypatch):
    monkeypatch.setattr(api, "load_prices", lambda tickers: _prices([100.0, 110.0]))
    response = TestClient(api.app).post("/risk", json={"weights": {"NVDA": 1}})
    assert response.status_code == 422
    assert "two finite daily portfolio returns" in response.json()["detail"]


def test_single_price_returns_validation_instead_of_json_serialization_crash(monkeypatch):
    monkeypatch.setattr(api, "load_prices", lambda tickers: _prices([100.0]))
    response = TestClient(api.app).post("/risk", json={"weights": {"NVDA": 1}})
    assert response.status_code == 422


def test_nonfinite_return_from_zero_price_is_rejected(monkeypatch):
    monkeypatch.setattr(api, "load_prices", lambda tickers: _prices([100.0, 0.0, 50.0]))
    response = TestClient(api.app).post("/risk", json={"weights": {"NVDA": 1}})
    assert response.status_code == 422


def test_three_finite_prices_still_return_valid_risk_json(monkeypatch):
    monkeypatch.setattr(api, "load_prices", lambda tickers: _prices([100.0, 110.0, 121.0]))
    response = TestClient(api.app).post("/risk", json={"weights": {"NVDA": 1}})
    assert response.status_code == 200
    assert isinstance(response.json()["volatility"], (float, int))
    assert response.json()["max_drawdown"] <= 0.0
