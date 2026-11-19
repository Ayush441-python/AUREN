import pytest
from fastapi.testclient import TestClient

import api
import engine.data as d


@pytest.fixture(autouse=True)
def mock_load_prices(monkeypatch):
    monkeypatch.setattr(api, "load_prices", lambda t: d._cached(d.CACHE, t))


@pytest.fixture
def client():
    return TestClient(api.app)


@pytest.mark.parametrize(
    "body",
    [
        '{"weights":{"NVDA":NaN,"MSFT":50}}',
        '{"weights":{"NVDA":Infinity,"MSFT":50}}',
        '{"weights":{"NVDA":-Infinity,"MSFT":50}}',
    ],
)
def test_non_finite_weights_rejected(client, body):
    r = client.post(
        "/risk", content=body, headers={"content-type": "application/json"}
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "Weights must be positive numbers summing to > 0"


def test_valid_portfolio_accepted(client):
    r = client.post(
        "/risk",
        json={"weights": {"NVDA": 40, "MSFT": 30, "GOOGL": 20, "ETH-USD": 10}},
    )
    assert r.status_code == 200
    data = r.json()
    assert "score" in data
    assert "level" in data
    assert "reasons" in data
