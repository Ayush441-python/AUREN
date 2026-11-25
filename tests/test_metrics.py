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
from engine.stress import SCENARIOS, stress
from engine.universe import classify_and_register_ticker


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


@pytest.mark.parametrize(
    "ticker",
    [
        "USDC-USD",
        "PYUSD-USD",
        "USDT-USD",
        "DAI-USD",
        "FDUSD-USD",
        "TUSD-USD",
        "USDP-USD",
        "GUSD-USD",
        "LUSD-USD",
        "BUSD-USD",
        "FRAX-USD",
        "USDE-USD",
        "USDS-USD",
        "RLUSD-USD",
        "EURC-USD",
    ],
)
def test_stablecoin_usd_pairs_classified_as_cash_not_crypto(ticker):
    sector, group = classify_and_register_ticker(ticker)
    assert sector == "Stablecoin"
    assert group == "Cash & Stablecoins"


def test_non_stablecoin_usd_pair_stays_crypto():
    sector, group = classify_and_register_ticker("XRP-USD")
    assert sector == "Crypto"
    assert group == "Crypto"


def test_pure_stablecoin_pair_has_zero_stress_across_all_scenarios():
    classify_and_register_ticker("PYUSD-USD")
    w = pd.Series([1.0], index=["PYUSD-USD"])
    exp = sector_exposure(w)
    assert exp.to_dict() == {"Cash & Stablecoins": pytest.approx(1.0)}
    for name, shocks in SCENARIOS.items():
        assert stress(w, shocks) == pytest.approx(0.0), f"Non-zero stress for {name}"


def test_half_crypto_half_stablecoin_pair_exposure_and_stress():
    classify_and_register_ticker("USDC-USD")
    w = pd.Series([0.5, 0.5], index=["DOGE-USD", "USDC-USD"])
    exp = sector_exposure(w)
    assert exp["Crypto"] == pytest.approx(0.5)
    assert exp["Cash & Stablecoins"] == pytest.approx(0.5)
    assert stress(w, SCENARIOS["Crypto crash 40%"]) == pytest.approx(-0.20)
    assert stress(w, SCENARIOS["Broad selloff"]) == pytest.approx(-0.15)
    # 50% max sector exposure must not trigger the > 50% sector concentration penalty
    _, _, hits = risk_score(concentration(w), 0.10, -0.05, [], float(exp.max()))
    assert not any("sits in one sector" in why for _, why in hits)
