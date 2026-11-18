"""Risk API regression: finite positive portfolio weights must not overflow."""
import json

import pandas as pd
import pytest
from fastapi.testclient import TestClient

import api


@pytest.fixture
def client(monkeypatch):
    prices = pd.DataFrame(
        {"NVDA": [100.0, 110.0, 105.0, 120.0],
         "MSFT": [80.0, 90.0, 92.0, 96.0]},
        index=pd.date_range("2026-11-12", periods=4, freq="D"),
    )
    monkeypatch.setattr(api, "load_prices", lambda tickers: prices[tickers])
    return TestClient(api.app)


def request(client, nvda, msft):
    return client.post("/risk", json={"weights": {"NVDA": nvda, "MSFT": msft}})


def test_float64_sum_overflow_is_still_a_valid_equal_weight_portfolio(client):
    result = request(client, 1e308, 1e308)
    assert result.status_code == 200, result.text
    metrics = result.json()["concentration"]
    assert metrics["top_weight"] == pytest.approx(0.5)
    assert metrics["hhi"] == pytest.approx(0.5)
    assert metrics["effective_assets"] == pytest.approx(2.0)


def test_extreme_weight_magnitudes_match_unscaled_portfolio(client):
    base = request(client, 1.0, 2.0)
    large = request(client, 4e307, 8e307)
    assert base.status_code == large.status_code == 200
    assert large.json()["score"] == base.json()["score"]
    assert large.json()["concentration"]["hhi"] == pytest.approx(
        base.json()["concentration"]["hhi"]
    )


def test_subnormal_positive_weights_can_be_normalized(client):
    result = request(client, 1e-310, 1e-310)
    assert result.status_code == 200, result.text
    assert result.json()["concentration"]["effective_assets"] == pytest.approx(2.0)


@pytest.mark.parametrize("nonfinite", ["NaN", "Infinity", "-Infinity"])
def test_nonfinite_values_rejected_with_http_400(client, nonfinite):
    body = '{"weights":{"NVDA":' + nonfinite + ',"MSFT":1}}'
    response = client.post(
        "/risk", content=body, headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 400
    assert "finite positive" in response.json()["detail"]


@pytest.mark.parametrize("nvda", [0.0, -1.0])
def test_zero_or_negative_weights_are_rejected(client, nvda):
    response = request(client, nvda, 1.0)
    assert response.status_code == 400