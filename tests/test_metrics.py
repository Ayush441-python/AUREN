import pandas as pd
import pytest
from engine.metrics import (
    concentration,
    correlation,
    high_pairs,
    max_drawdown,
    portfolio_returns,
    sector_exposure,
    volatility,
)
from engine.score import risk_score
from engine.stress import stress, worst_periods


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


def test_portfolio_returns_buy_and_hold_default():
    # Asset A doubles (+100%), Asset B is flat (0%)
    # Equal weight 50/50: V_0 = 1.0, V_1 = 0.5(2.0) + 0.5(1.0) = 1.5 -> +50%
    # Next day: Asset A rises from 200 to 250 (+25%), B stays flat
    # V_2 = 0.5(2.5) + 0.5(1.0) = 1.75 -> return is 1.75 / 1.5 - 1 = +16.6667%
    # Under constant-mix rebalancing: 0.5(+25%) + 0.5(0%) = +12.5%
    prices = pd.DataFrame({
        "A": [100.0, 200.0, 250.0],
        "B": [100.0, 100.0, 100.0],
    })
    w = pd.Series({"A": 0.5, "B": 0.5})
    pr_bh = portfolio_returns(prices, w)
    pr_cm = portfolio_returns(prices, w, rebalance_daily=True)

    assert pr_bh.iloc[0] == pytest.approx(0.50)
    assert pr_bh.iloc[1] == pytest.approx(1.75 / 1.5 - 1.0)
    assert pr_cm.iloc[0] == pytest.approx(0.50)
    assert pr_cm.iloc[1] == pytest.approx(0.125)


def test_portfolio_returns_single_asset_identical():
    prices = pd.DataFrame({"A": [100.0, 105.0, 95.0, 110.0, 108.0]})
    w = pd.Series({"A": 1.0})
    pr_bh = portfolio_returns(prices, w, rebalance_daily=False)
    pr_cm = portfolio_returns(prices, w, rebalance_daily=True)
    expected = prices["A"].pct_change().dropna()

    pd.testing.assert_series_equal(pr_bh, pr_cm, check_names=False)
    pd.testing.assert_series_equal(pr_bh, expected, check_names=False)


def test_shannons_demon_oscillation_rebalancing_artifact():
    osc = pd.DataFrame({
        "A": [100.0, 200.0, 100.0, 50.0, 100.0, 200.0, 100.0, 50.0],
        "B": [100.0,  50.0, 100.0, 200.0, 100.0, 50.0, 100.0, 200.0],
    })
    w = pd.Series({"A": 0.5, "B": 0.5})
    pr_cm = portfolio_returns(osc, w, rebalance_daily=True)
    pr_bh = portfolio_returns(osc, w, rebalance_daily=False)

    assert volatility(pr_cm) == pytest.approx(0.0)
    assert max_drawdown(pr_cm) == pytest.approx(0.0)
    assert volatility(pr_bh) == pytest.approx(3.8184, rel=1e-3)
    assert max_drawdown(pr_bh) == pytest.approx(-0.20, rel=1e-3)


def test_portfolio_returns_winner_concentration_drift_real_data():
    prices = pd.read_csv("data/prices.csv", index_col=0, parse_dates=True)
    w = pd.Series({"MU": 0.25, "COST": 0.25, "PEP": 0.25, "XEL": 0.25})

    pr_bh = portfolio_returns(prices, w)
    pr_cm = portfolio_returns(prices, w, rebalance_daily=True)

    vol_bh = volatility(pr_bh)
    mdd_bh = max_drawdown(pr_bh)
    wp_bh = worst_periods(pr_bh)

    assert vol_bh == pytest.approx(0.4218, abs=1e-3)
    assert mdd_bh == pytest.approx(-0.3551, abs=1e-3)
    assert wp_bh["worst_day"] == pytest.approx(-0.1221, abs=1e-3)
    assert wp_bh["worst_month"] == pytest.approx(-0.2860, abs=1e-3)

    c = concentration(w)
    pairs = high_pairs(correlation(prices, w.index))
    sec = float(sector_exposure(w).max())
    score_bh, lvl_bh, _ = risk_score(c, vol_bh, mdd_bh, pairs, sec)
    score_cm, lvl_cm, _ = risk_score(c, volatility(pr_cm), max_drawdown(pr_cm), pairs, sec)

    assert score_bh == 35 and lvl_bh == "Medium"
    assert score_cm == 0 and lvl_cm == "Low"

    # Additional check: MU 30% / COST 70% (score 85 High vs 50 Medium)
    w_mu_cost = pd.Series({"MU": 0.30, "COST": 0.70})
    pr_mu_cost_bh = portfolio_returns(prices, w_mu_cost)
    pr_mu_cost_cm = portfolio_returns(prices, w_mu_cost, rebalance_daily=True)
    c_mc = concentration(w_mu_cost)
    pairs_mc = high_pairs(correlation(prices, w_mu_cost.index))
    sec_mc = float(sector_exposure(w_mu_cost).max())
    s_mc_bh, lvl_mc_bh, _ = risk_score(
        c_mc, volatility(pr_mu_cost_bh), max_drawdown(pr_mu_cost_bh), pairs_mc, sec_mc
    )
    s_mc_cm, lvl_mc_cm, _ = risk_score(
        c_mc, volatility(pr_mu_cost_cm), max_drawdown(pr_mu_cost_cm), pairs_mc, sec_mc
    )
    assert volatility(pr_mu_cost_bh) == pytest.approx(0.4655, abs=1e-3)
    assert max_drawdown(pr_mu_cost_bh) == pytest.approx(-0.3631, abs=1e-3)
    assert s_mc_bh == 85 and lvl_mc_bh == "High"
    assert s_mc_cm == 50 and lvl_mc_cm == "Medium"

    # Additional check: PLTR 30% / COST 70% (score 70 High vs 50 Medium)
    w_pltr_cost = pd.Series({"PLTR": 0.30, "COST": 0.70})
    pr_pc_bh = portfolio_returns(prices, w_pltr_cost)
    pr_pc_cm = portfolio_returns(prices, w_pltr_cost, rebalance_daily=True)
    c_pc = concentration(w_pltr_cost)
    pairs_pc = high_pairs(correlation(prices, w_pltr_cost.index))
    sec_pc = float(sector_exposure(w_pltr_cost).max())
    s_pc_bh, lvl_pc_bh, _ = risk_score(
        c_pc, volatility(pr_pc_bh), max_drawdown(pr_pc_bh), pairs_pc, sec_pc
    )
    s_pc_cm, lvl_pc_cm, _ = risk_score(
        c_pc, volatility(pr_pc_cm), max_drawdown(pr_pc_cm), pairs_pc, sec_pc
    )
    assert volatility(pr_pc_bh) == pytest.approx(0.3230, abs=1e-3)
    assert max_drawdown(pr_pc_bh) == pytest.approx(-0.2762, abs=1e-3)
    assert s_pc_bh == 70 and lvl_pc_bh == "High"
    assert s_pc_cm == 50 and lvl_pc_cm == "Medium"


def test_portfolio_returns_cumprod_wealth_identity():
    prices = pd.read_csv("data/prices.csv", index_col=0, parse_dates=True)
    w = pd.Series({"MU": 0.30, "COST": 0.70})
    pr = portfolio_returns(prices, w)
    aligned = prices[w.index].dropna()
    wealth = (aligned / aligned.iloc[0]) @ w
    assert (1 + pr).cumprod().values == pytest.approx(wealth.iloc[1:].values)


def test_portfolio_returns_insufficient_data():
    empty_df = pd.DataFrame(columns=["A", "B"])
    w = pd.Series({"A": 0.5, "B": 0.5})
    assert portfolio_returns(empty_df, w).empty
    assert portfolio_returns(empty_df, w, rebalance_daily=True).empty

    single_row = pd.DataFrame({"A": [100.0], "B": [200.0]})
    assert portfolio_returns(single_row, w).empty
    assert portfolio_returns(single_row, w, rebalance_daily=True).empty
