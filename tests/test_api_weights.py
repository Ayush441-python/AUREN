import api
import engine.data as d
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def mock_load_prices():
    api.load_prices = lambda t: d._cached(d.CACHE, t)


@pytest.mark.parametrize(
    "body",
    [
        '{"weights":{"NVDA":NaN,"MSFT":50}}',
        '{"weights":{"NVDA":Infinity,"MSFT":50}}',
        '{"weights":{"NVDA":-Infinity,"MSFT":50}}',
    ],
)
def test_non_finite_weights_rejected(body):
    c = TestClient(api.app, raise_server_exceptions=False)
    r = c.post(
        "/risk",
        content=body,
        headers={"content-type": "application/json"},
    )
    assert r.status_code == 400
    assert "positive numbers" in r.json()["detail"]


def test_valid_weights_accepted():
    c = TestClient(api.app, raise_server_exceptions=False)
    r = c.post(
        "/risk",
        json={"weights": {"NVDA": 50, "MSFT": 50}},
    )
    assert r.status_code == 200
    data = r.json()
    assert "score" in data
    assert "level" in data
