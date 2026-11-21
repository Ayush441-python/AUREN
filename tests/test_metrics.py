import pandas as pd
import pytest
from engine.metrics import (
    concentration,
    volatility,
    max_drawdown,
    correlation,
    high_pairs,
    sector_exposure,
)
from engine.score import risk_score
from engine.stress import stress
from engine.universe import SECTORS
import engine.wallet as wallet_mod


def test_equal_weights_effective_assets():
    w = pd.Series([0.25] * 4, index=list("ABCD"))
    assert concentration(w)["effective_assets"] == pytest.approx(4)


def test_drawdown_known_case():
    pr = pd.Series([0.10, -0.50, 0.20])  # 1.10 -> 0.55 -> 0.66
    assert max_drawdown(pr) == pytest.approx(-0.5)


def test_no_swings_no_volatility():
    assert volatility(pd.Series([0.01] * 10)) == pytest.approx(0)


def test_perfectly_correlated_assets():
    prices = pd.DataFrame(
        {"A": [100, 101, 103, 102, 105], "B": [200, 202, 206, 204, 210]}
    )  # B = 2 x A
    corr = correlation(prices, ["A", "B"])
    assert corr.loc["A", "B"] == pytest.approx(1.0)


def test_high_pairs_finds_the_pair():
    prices = pd.DataFrame(
        {"A": [100, 101, 103, 102, 105], "B": [200, 202, 206, 204, 210]}
    )
    corr = correlation(prices, ["A", "B"])
    assert high_pairs(corr) == [("A", "B", 1.0)]


def test_safe_portfolio_scores_zero():
    conc = {"top_weight": 0.10, "effective_assets": 10}
    score, level, hits = risk_score(conc, 0.10, -0.05, [], 0.20)
    assert score == 0 and level == "Low" and hits == []


def test_worst_case_scores_100():
    conc = {"top_weight": 0.60, "effective_assets": 1.5}
    pairs = [("A", "B", 0.9), ("A", "C", 0.8)]
    score, level, hits = risk_score(conc, 0.50, -0.50, pairs, 0.80)
    assert score == 100 and level == "High"


def test_single_rule_adds_its_points():
    conc = {"top_weight": 0.40, "effective_assets": 10}
    score, _, hits = risk_score(conc, 0.10, -0.05, [], 0.20)
    assert score == 20 and len(hits) == 1


def test_sector_exposure_tech():
    # Day 9 test from playbook: NVDA 50% + MSFT 50% gives Big Tech = 100%
    w = pd.Series([0.5, 0.5], index=["NVDA", "MSFT"])
    exp = sector_exposure(w)
    assert exp.get("Big Tech", 0) == pytest.approx(1.0)


def test_stress_scenario():
    # Day 11 test from playbook: 50% NVDA + 50% GLD in "Big Tech falls 20%" = -10%
    w = pd.Series([0.5, 0.5], index=["NVDA", "GLD"])
    shocks = {"Big Tech": -0.20}
    assert stress(w, shocks) == pytest.approx(-0.10)


def test_wallet_holdings_resolves_missing_nav_price_with_multiplier(monkeypatch):
    # Coinbase /v1/tokenized-stocks omits nav_price for 12 of the 20 supported tickers (e.g. AMDc, ORCLc)
    mock_tokens = [
        {
            "contract_address": "0x1111111111111111111111111111111111111111",
            "symbol": "NVDAc",
            "decimals": 8,
            "multiplier": 1.0,
            "nav_price": 200.0,
        },
        {
            "contract_address": "0x2222222222222222222222222222222222222222",
            "symbol": "AMDc",
            "decimals": 8,
            "multiplier": 1.0,
            "nav_price": None,
        },
        {
            "contract_address": "0x3333333333333333333333333333333333333333",
            "symbol": "ORCLc",
            "decimals": 8,
            "multiplier": 1.05,
            "nav_price": None,
        },
    ]
    monkeypatch.setattr(wallet_mod, "list_tokenized_stocks", lambda timeout=20: mock_tokens)
    monkeypatch.setattr(
        wallet_mod,
        "token_balances",
        lambda wallet, tokens, rpc_url=wallet_mod.BASE_RPC: {
            "0x1111111111111111111111111111111111111111": 25.0,
            "0x2222222222222222222222222222222222222222": 10.0,
            "0x3333333333333333333333333333333333333333": 20.0,
        },
    )

    info = wallet_mod.wallet_holdings(
        "0x9EfdeD16BCc89819dd328b6958d4262aB1234acf",
        set(SECTORS),
        fallback_prices={"AMD": 500.0, "ORCL": 100.0},
    )
    by_ticker = {r["ticker"]: r for r in info["rows"]}
    assert by_ticker["NVDA"]["value"] == pytest.approx(5000.0)
    assert by_ticker["AMD"]["price"] == pytest.approx(500.0)
    assert by_ticker["AMD"]["value"] == pytest.approx(5000.0)
    # ORCLc has multiplier 1.05 -> 20 tokens = 21 shares @ $100 = $2,100 ($105/token)
    assert by_ticker["ORCL"]["shares"] == pytest.approx(21.0)
    assert by_ticker["ORCL"]["price"] == pytest.approx(105.0)
    assert by_ticker["ORCL"]["value"] == pytest.approx(2100.0)


def test_holdings_to_portfolio_retains_supported_tokens_missing_nav():
    rows = [
        {
            "token": "NVDAc", "ticker": "NVDA", "address": "0x1",
            "tokens": 25.0, "shares": 25.0, "price": 200.0, "value": 5000.0,
            "supported": True,
        },
        {
            "token": "AMDc", "ticker": "AMD", "address": "0x2",
            "tokens": 10.0, "shares": 10.0, "price": 0.0, "value": 0.0,
            "supported": True,
        },
    ]
    df, total, skipped = wallet_mod.holdings_to_portfolio(rows, fallback_prices={"AMD": 500.0})
    assert skipped == []
    assert total == pytest.approx(10000.0)
    weights = pd.Series(df["weight"].values / 100.0, index=df["ticker"].values)
    assert weights["NVDA"] == pytest.approx(0.50)
    assert weights["AMD"] == pytest.approx(0.50)
    assert concentration(weights)["effective_assets"] == pytest.approx(2.0)


def test_wallet_holdings_falls_back_to_cached_prices_csv(monkeypatch):
    # Without explicit fallback_prices, wallet_holdings resolves missing nav_price from data/prices.csv
    mock_tokens = [
        {
            "contract_address": "0xb2000000000000000000000d8ce462e99ee7a47b",
            "symbol": "AMDc",
            "decimals": 8,
            "multiplier": 1.0,
            "nav_price": None,
        },
        {
            "contract_address": "0xb200000000000000000000000000000000000001",
            "symbol": "MUc",
            "decimals": 8,
            "multiplier": 1.0001006811764792,
            "nav_price": None,
        },
    ]
    monkeypatch.setattr(wallet_mod, "list_tokenized_stocks", lambda timeout=20: mock_tokens)
    monkeypatch.setattr(
        wallet_mod,
        "token_balances",
        lambda wallet, tokens, rpc_url=wallet_mod.BASE_RPC: {
            "0xb2000000000000000000000d8ce462e99ee7a47b": 2.0,
            "0xb200000000000000000000000000000000000001": 1.0,
        },
    )
    info = wallet_mod.wallet_holdings("0x9EfdeD16BCc89819dd328b6958d4262aB1234acf", set(SECTORS))
    df, total, skipped = wallet_mod.holdings_to_portfolio(info["rows"])
    assert skipped == []
    assert len(df) == 2
    assert total > 1500.0
    assert float(df["weight"].sum()) == pytest.approx(100.0)


