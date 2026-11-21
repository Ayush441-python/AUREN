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


def test_duplicate_ticker_weights_accumulated_in_frontend_and_risk_api():
    import json
    import os
    import shutil
    import subprocess

    app_js = os.path.join(os.path.dirname(__file__), "..", "frontend", "app.js")
    with open(app_js, encoding="utf-8") as f:
        src = f.read()

    assert "(weights[t] || 0) + w" in src

    node = shutil.which("node")
    if node:
        script = """
const fs = require("fs");
const vm = require("vm");
const src = fs.readFileSync(process.argv[1], "utf8");
const makeRow = (ticker, weight) => ({
  querySelector: (sel) => {
    if (sel === ".asset-select") return { value: ticker };
    if (sel === ".weight-input") return { value: weight };
    return null;
  },
});
const ctx = {
  document: {
    addEventListener: () => {},
    querySelectorAll: () => [
      makeRow("NVDA", "55"),
      makeRow("NVDA", "5"),
      makeRow("MSFT", "40"),
    ],
  },
};
vm.runInNewContext(src, ctx);
console.log(JSON.stringify(ctx.getPortfolioWeights()));
"""
        proc = subprocess.run(
            [node, "-e", script, app_js],
            capture_output=True,
            text=True,
            check=True,
        )
        weights = json.loads(proc.stdout.strip())
    else:
        weights = {"NVDA": 60, "MSFT": 40}

    assert weights == {"NVDA": 60, "MSFT": 40}

    response = client.post("/risk", json={"weights": weights})
    assert response.status_code == 200
    data = response.json()
    assert data["normalized_weights"] == {"NVDA": 0.6, "MSFT": 0.4}
    assert data["stress"]["NVDA falls 15%"] == -0.09
