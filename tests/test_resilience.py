import pytest
from fastapi.testclient import TestClient
from backend.app.main import app, _normalize_and_validate_weights
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
    for t in tokens:
        assert t["contract_address"].lower().startswith("0xb20")
        assert len(t["contract_address"]) == 42
        assert t["decimals"] == 8


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
    import backend.app.main as api_mod
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
    import backend.app.main as api_mod
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


def test_b20_multiplier_and_dynamic_pricing(monkeypatch):
    import engine.wallet as wallet_mod

    test_token = {
        "symbol": "NVDAc",
        "ticker": "NVDA",
        "contract_address": "0xb20000000000000000000078ee7ce2fe4908108c",
        "decimals": 8,
        "nav_price": 150.0,
        "multiplier": 2.5,
    }
    monkeypatch.setattr(wallet_mod, "list_tokenized_stocks", lambda: [test_token])
    monkeypatch.setattr(wallet_mod, "KNOWN_BASE_TOKENS", [])
    monkeypatch.setattr(
        wallet_mod,
        "token_balances",
        lambda w, t, rpc_url=None: {"0xb20000000000000000000078ee7ce2fe4908108c": 4.0},
    )
    monkeypatch.setattr(wallet_mod, "get_native_eth_balance", lambda w, rpcs=None: 1.0)
    monkeypatch.setattr(
        wallet_mod,
        "get_latest_prices",
        lambda tickers: ({"NVDA": 160.0, "ETH-USD": 2000.0}, "2026-11-17T21:00:00Z"),
    )

    info = wallet_mod.wallet_holdings("0x" + "2" * 40, set(SECTORS))
    rows = {r["token"]: r for r in info["rows"]}
    # 4.0 tokens * 2.5 multiplier = 10.0 shares; 10.0 shares * $160.0 = $1600.0
    assert rows["NVDAc"]["shares"] == pytest.approx(10.0)
    assert rows["NVDAc"]["price"] == pytest.approx(160.0)
    assert rows["NVDAc"]["value"] == pytest.approx(1600.0)
    assert rows["ETH"]["price"] == pytest.approx(2000.0)
    assert rows["ETH"]["value"] == pytest.approx(2000.0)


def test_known_base_tokens_and_risk_for_base_ecosystem():
    from engine.wallet import KNOWN_BASE_TOKENS

    symbols = {t["symbol"] for t in KNOWN_BASE_TOKENS}
    assert {"cbBTC", "USDC", "WETH", "AERO", "VIRTUAL"}.issubset(symbols)

    res = client.post(
        "/risk",
        json={"weights": {"NVDA": 40, "AERO": 20, "VIRTUAL": 20, "USDC": 20}},
    )
    assert res.status_code == 200
    data = res.json()
    assert "score" in data
    assert "AERO-USD" in data["normalized_weights"]
    assert "VIRTUAL-USD" in data["normalized_weights"]
    assert "USDC" in data["normalized_weights"]
    assert round(sum(data["normalized_weights"].values()), 2) == 1.0


def test_erc8021_builder_code_encoding_and_decoding():
    from engine.wallet import (
        encode_erc8021_suffix,
        encode_risk_attestation_calldata,
        decode_erc8021_calldata,
    )

    # Exact canonical test vector from ERC-8021 specification for "bc_c4zqoeov"
    suffix = encode_erc8021_suffix("bc_c4zqoeov")
    assert suffix == "62635f63347a716f656f760b0080218021802180218021802180218021"

    attest = encode_risk_attestation_calldata(
        score=28,
        level="Low",
        top_asset="NVDA",
        portfolio_name="Base Tokenized Stocks",
        builder_code="bc_c4zqoeov",
        timestamp=1795700000,
    )
    assert attest["chain_id"] == 8453
    assert attest["calldata"].endswith(suffix)

    decoded = decode_erc8021_calldata(attest["calldata"])
    assert decoded["erc8021_verified"] is True
    assert decoded["builder_code"] == "bc_c4zqoeov"
    assert decoded["is_auren_audit"] is True
    assert "score=28|level=Low|top=NVDA" in decoded["payload_text"]

    # Verify API endpoints /attest/encode and /attest/decode
    enc_res = client.post(
        "/attest/encode",
        json={
            "score": 32,
            "level": "Low",
            "top_asset": "NVDA",
            "portfolio_name": "Base RWA",
            "builder_code": "bc_c4zqoeov",
        },
    )
    assert enc_res.status_code == 200
    enc_data = enc_res.json()
    assert enc_data["chain_id"] == 8453
    assert enc_data["calldata"].endswith(suffix)

    dec_res = client.post("/attest/decode", json={"calldata": enc_data["calldata"]})
    assert dec_res.status_code == 200
    dec_data = dec_res.json()
    assert dec_data["erc8021_verified"] is True
    assert dec_data["builder_code"] == "bc_c4zqoeov"
    assert dec_data["is_auren_audit"] is True


def test_o1_exchange_alpha_tokens_and_deterministic_rebalance():
    # 1. Test GET /o1/alpha-tokens?networkId=8453
    alpha_res = client.get("/o1/alpha-tokens?networkId=8453")
    assert alpha_res.status_code == 200
    alpha_data = alpha_res.json()
    assert alpha_data["network_id"] == 8453
    assert alpha_data["count"] >= 10
    assert any(addr.startswith("0xb20") for addr in alpha_data["addresses"])

    # Invalid networkId should return 400 per o1 Exchange spec
    bad_res = client.get("/o1/alpha-tokens?networkId=0")
    assert bad_res.status_code == 400

    # 2. Test POST /rebalance on a concentrated portfolio
    reb_res = client.post(
        "/rebalance",
        json={
            "weights": {"NVDA": 70, "ETH-USD": 30},
            "portfolio_value": 100000.0,
            "builder_code": "bc_c4zqoeov",
        },
    )
    assert reb_res.status_code == 200
    plan = reb_res.json()
    assert plan["network_id"] == 8453
    assert plan["after"]["score"] < plan["before"]["score"]
    assert plan["score_reduction"] > 0
    assert plan["after"]["top_weight"] <= 0.30
    assert plan["after"]["effective_assets"] >= 4.0
    assert len(plan["trades"]) >= 2

    bundle = plan["o1_order_bundle"]
    assert bundle["networkId"] == 8453
    assert bundle["mevProtection"] is True
    assert bundle["permit2"] is True
    assert len(bundle["orders"]) == len(plan["trades"])
    assert bundle["orders"][0]["erc8021BuilderCode"] == "bc_c4zqoeov"



