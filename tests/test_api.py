from unittest.mock import patch
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

def test_wallet_valid():
    token = "0x" + "2" * 40
    catalog = [{"symbol": "NVDAc", "contract_address": token, "nav_price": "125"}]
    with patch("engine.wallet.list_tokenized_stocks", return_value=catalog), patch(
        "engine.wallet.token_balances", return_value={token: 2.0}
    ):
        response = client.post("/wallet", json={"address": "0x" + "1" * 40})
        assert response.status_code == 200
        data = response.json()
        assert data["address"] == "0x" + "1" * 40
        assert data["holdings_count"] == 1
        assert len(data["holdings"]) == 1
        assert data["holdings"][0]["ticker"] == "NVDA"
        assert data["holdings"][0]["value"] == 250.0
        assert data["holdings"][0]["supported"] is True
        assert data["portfolio"] == {"NVDA": 1.0}

def test_wallet_valid_multiple_and_unsupported():
    token1 = "0x" + "2" * 40
    token2 = "0x" + "3" * 40
    token3 = "0x" + "4" * 40
    catalog = [
        {"symbol": "NVDAc", "contract_address": token1, "nav_price": "100"},
        {"symbol": "MSFTc", "contract_address": token2, "nav_price": "100"},
        {"symbol": "FAKEc", "contract_address": token3, "nav_price": "50"},
    ]
    balances = {token1: 1.0, token2: 3.0, token3: 2.0}
    with patch("engine.wallet.list_tokenized_stocks", return_value=catalog), patch(
        "engine.wallet.token_balances", return_value=balances
    ):
        response = client.post("/wallet", json={"address": "0x" + "1" * 40})
        assert response.status_code == 200
        data = response.json()
        assert data["holdings_count"] == 3
        # NVDA value = 100, MSFT value = 300, total supported value = 400
        # FAKE is unsupported (not in SECTORS)
        assert data["portfolio"] == {"NVDA": 0.25, "MSFT": 0.75}

def test_wallet_empty():
    token = "0x" + "2" * 40
    catalog = [{"symbol": "NVDAc", "contract_address": token, "nav_price": "125"}]
    with patch("engine.wallet.list_tokenized_stocks", return_value=catalog), patch(
        "engine.wallet.token_balances", return_value={}
    ):
        response = client.post("/wallet", json={"address": "0x" + "1" * 40})
        assert response.status_code == 200
        data = response.json()
        assert data["holdings_count"] == 0
        assert data["holdings"] == []
        assert data["portfolio"] == {}

def test_wallet_rpc_error():
    with patch("engine.wallet.list_tokenized_stocks", side_effect=RuntimeError("RPC connection timeout")):
        response = client.post("/wallet", json={"address": "0x" + "1" * 40})
        assert response.status_code == 502
        assert "Error querying on-chain wallet data: RPC connection timeout" in response.json()["detail"]

