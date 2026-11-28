import pytest
from fastapi.testclient import TestClient
from api import app
from engine.data import STABLECOIN_TICKERS, load_prices, load_volumes
from engine.liquidity import avg_daily_value

client = TestClient(app)


def test_stablecoin_tickers_defined():
    expected = {"USDC", "USDT", "DAI", "USD", "BUSD"}
    assert expected.issubset(STABLECOIN_TICKERS)


def test_pure_usdc_portfolio_volatility_and_scoring():
    response = client.post(
        "/risk",
        json={"weights": {"USDC": 100.0}},
    )
    assert response.status_code == 200
    data = response.json()

    # Volatility must be 0.0%
    assert data["volatility"] == 0.0
    assert data["max_drawdown"] == 0.0

    # Score should be 50 (100% concentration [20pts] + 1 effective asset [15pts] + 100% single sector [15pts])
    assert data["score"] == 50
    assert data["level"] == "Medium"

    # Zero volatility penalty points
    assert not any("volatility" in why.lower() for why in data["reasons"])
    assert not any(pts == 20 and "volatility" in why.lower() for pts, why in data["hits"])

    # Price series constant 100.0
    assert all(p == 100.0 for p in data["price_series"]["USDC"])
    assert all(p == 100.0 for p in data["price_series"]["Portfolio"])


def test_macro_defensive_reserve_volatility_proportional_scaling():
    # 1. Base risky portfolio without USDC: SPY 40%, GLD 30%, QQQ 20%
    resp_no_usdc = client.post(
        "/risk",
        json={"weights": {"SPY": 40.0, "GLD": 30.0, "QQQ": 20.0}},
    )
    assert resp_no_usdc.status_code == 200
    vol_no_usdc = resp_no_usdc.json()["volatility"]
    assert 0.15 < vol_no_usdc < 0.18

    # 2. Macro Defensive Reserve with 10% USDC: SPY 40%, GLD 30%, QQQ 20%, USDC 10%
    resp_defensive = client.post(
        "/risk",
        json={"weights": {"SPY": 40.0, "GLD": 30.0, "QQQ": 20.0, "USDC": 10.0}},
    )
    assert resp_defensive.status_code == 200
    vol_defensive = resp_defensive.json()["volatility"]

    # Volatility should scale down by 0.9 (approx 14.9%) rather than jump to 80.19%
    assert vol_defensive == pytest.approx(vol_no_usdc * 0.9, rel=1e-3)
    assert vol_defensive < 0.20
    assert resp_defensive.json()["score"] <= 55


def test_stablecoin_offline_resilience_and_liquidity():
    # Stablecoin loads without 502 even if offline
    prices = load_prices(["USDC"])
    volumes = load_volumes(["USDC"])
    assert not prices.empty
    assert not volumes.empty
    assert (prices["USDC"] == 1.0).all()
    assert (volumes["USDC"] == 5_000_000_000.0).all()

    # Direct avg_daily_value check
    adv = avg_daily_value(prices, volumes)
    assert "USDC" in adv
    assert adv["USDC"] == pytest.approx(5_000_000_000.0)

    # Liquidity endpoint works cleanly for USDC
    resp_liq = client.post(
        "/liquidity",
        json={"portfolio_value": 100000.0, "weights": {"USDC": 100.0}},
    )
    assert resp_liq.status_code == 200
    liq_data = resp_liq.json()
    assert len(liq_data["assets"]) == 1
    assert liq_data["assets"][0]["ticker"] == "USDC"
    assert liq_data["assets"][0]["adv"] == pytest.approx(5_000_000_000.0)


def test_mixed_stablecoins_determinism():
    # Multiple stablecoins together
    resp = client.post(
        "/risk",
        json={"weights": {"USDC": 50.0, "USDT": 50.0}},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["volatility"] == 0.0
    assert data["max_drawdown"] == 0.0
