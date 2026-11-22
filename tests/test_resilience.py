import pytest
from fastapi.testclient import TestClient
from api import app, _normalize_and_validate_weights
from engine.universe import SECTORS, GROUPS, classify_and_register_ticker
from engine.wallet import (
    list_tokenized_stocks,
    holdings_to_portfolio,
    is_valid_address,
    load_bundled_tokens,
)

client = TestClient(app)


def test_bundled_token_registry_exists_and_loads():
    tokens = load_bundled_tokens()
    assert len(tokens) >= 10
    symbols = [t["symbol"] for t in tokens]
    assert "NVDAc" in symbols
    assert "AAPLc" in symbols


def test_list_tokenized_stocks_fallback_resilience(monkeypatch):
    import engine.wallet as wallet_mod
    # Simulate network outage on Coinbase endpoint
    monkeypatch.setattr(wallet_mod, "API_URL", "https://invalid-nonexistent-endpoint-12345.com")
    tokens = list_tokenized_stocks(timeout=1)
    assert len(tokens) >= 10
    assert any(t["symbol"] == "NVDAc" for t in tokens)


def test_dynamic_ticker_classification():
    sec, grp = classify_and_register_ticker("SPY")
    assert "SPY" in SECTORS
    assert "SPY" in GROUPS
    assert grp == "Broad Market ETFs"


def test_crypto_aliasing_in_weights():
    # User types "ETH" and "NVDA", should automatically resolve to "ETH-USD"
    w = _normalize_and_validate_weights({"ETH": 50, "NVDA": 50})
    assert "ETH-USD" in w.index
    assert "NVDA" in w.index
    assert w["ETH-USD"] == pytest.approx(0.5)


def test_empty_wallet_endpoint_graceful_handling(monkeypatch):
    import api as api_mod
    monkeypatch.setattr(
        api_mod,
        "wallet_holdings",
        lambda addr, supported, rpc: {"rows": [], "n_tokens": 10},
    )
    res = client.post("/wallet", json={"address": "0x" + "0" * 40})
    assert res.status_code == 200
    data = res.json()
    assert data["has_holdings"] is False
    assert data["holdings_count"] == 0
    assert data["portfolio"] == {}
    assert "No supported" in data["message"]


def test_wallet_with_native_eth_and_cbbtc(monkeypatch):
    import api as api_mod
    rows = [
        {
            "token": "ETH",
            "ticker": "ETH-USD",
            "address": "native-base",
            "tokens": 2.5,
            "shares": 2.5,
            "price": 3000.0,
            "value": 7500.0,
            "supported": True,
            "nav_updated": None,
        },
        {
            "token": "cbBTC",
            "ticker": "BTC-USD",
            "address": "0xcbb",
            "tokens": 0.1,
            "shares": 0.1,
            "price": 95000.0,
            "value": 9500.0,
            "supported": True,
            "nav_updated": None,
        },
    ]
    monkeypatch.setattr(
        api_mod,
        "wallet_holdings",
        lambda addr, supported, rpc: {"rows": rows, "n_tokens": 12},
    )
    res = client.post("/wallet", json={"address": "0x" + "1" * 40})
    assert res.status_code == 200
    data = res.json()
    assert data["has_holdings"] is True
    assert data["holdings_count"] == 2
    assert "ETH-USD" in data["portfolio"]
    assert "BTC-USD" in data["portfolio"]
    assert round(sum(data["portfolio"].values()), 2) == 1.0
