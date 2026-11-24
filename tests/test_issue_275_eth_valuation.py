from pathlib import Path
from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient

import api
import engine.wallet as wallet


def test_native_eth_uses_dated_market_price():
    """Verify that native ETH import uses the latest dated market price from prices.csv
    when available, rather than a hardcoded static $3,300 estimate."""
    stock_address = "0x" + "1" * 40
    stock = {
        "contract_address": stock_address,
        "symbol": "MSFTc",
        "ticker": "MSFT",
        "nav_price": 250.0,
        "multiplier": 1.0,
    }
    history = pd.read_csv(Path("data/prices.csv"), usecols=["Date", "ETH-USD"])
    reference = history.dropna(subset=["ETH-USD"]).iloc[-1]
    reference_price = float(reference["ETH-USD"])
    reference_date = str(reference["Date"])
    stock_value = 10 * stock["nav_price"]
    eth_weight = reference_price / (reference_price + stock_value)

    market_closes = pd.DataFrame(
        {"ETH-USD": range(100, 133), "MSFT": range(200, 233)},
        index=pd.bdate_range("2026-01-02", periods=33),
    )

    with (
        patch.object(wallet, "list_tokenized_stocks", return_value=[stock]),
        patch.object(wallet, "token_balances", return_value={stock_address: 10.0}),
        patch.object(wallet, "get_native_eth_balance", return_value=1.0),
        patch.object(api, "load_prices", return_value=market_closes),
        TestClient(api.app) as client,
    ):
        imported = client.post("/wallet", json={"address": "0x" + "0" * 40})
        imported.raise_for_status()
        data = imported.json()
        portfolio = data["portfolio"]
        
        eth = next(item for item in data["holdings"] if item["ticker"] == "ETH-USD")
        
        # Must reflect the latest dated market price
        assert eth["price"] == reference_price, f"Expected {reference_price}, got {eth['price']}"
        assert eth["nav_updated"] == reference_date, f"Expected date {reference_date}, got {eth.get('nav_updated')}"
        
        # Portfolio weight must align with reference price valuation
        expected_eth_weight = round(eth_weight, 6)
        assert abs(portfolio["ETH-USD"] - expected_eth_weight) < 1e-4

        # Risk endpoint identification of largest holding must match reference close
        risk = client.post("/risk", json={"weights": portfolio})
        risk.raise_for_status()
        assert risk.json()["concentration"]["top_asset"] == "MSFT"
