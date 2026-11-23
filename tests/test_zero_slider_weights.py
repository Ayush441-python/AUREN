from fastapi.testclient import TestClient
from api import app

client = TestClient(app)


def test_zero_slider_weight_normalization():
    # Moving any position slider to 0% should filter it out and succeed with 200 OK
    res = client.post("/risk", json={"weights": {"NVDA": 50, "MSFT": 0}})
    assert res.status_code == 200
    data = res.json()
    assert "MSFT" not in data["normalized_weights"]
    assert data["normalized_weights"]["NVDA"] == 1.0


def test_all_zero_weights_rejected():
    res = client.post("/risk", json={"weights": {"NVDA": 0, "MSFT": 0}})
    assert res.status_code == 400
    assert "positive numbers summing to > 0" in res.json()["detail"]


def test_negative_weights_rejected():
    res = client.post("/risk", json={"weights": {"NVDA": -10, "MSFT": 20}})
    assert res.status_code == 400
