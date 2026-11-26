import sys
import types

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

import api as api_module
from api import app
from engine.stress import SCENARIOS, shock_for, stress
from engine.universe import GROUPS, SECTORS, classify_and_register_ticker

client = TestClient(app)


def test_chip_selloff_covers_snps_and_all_semiconductor_tickers():
    shocks = SCENARIOS["Chip selloff (semis fall 25%)"]
    expected_chip_tickers = [
        "NVDA", "AVGO",
        "AMD", "INTC", "QCOM", "MU", "ARM", "TSM",
        "ASML", "AMAT", "LRCX", "ADI", "MRVL", "TXN",
        "SNPS",
    ]
    for ticker in expected_chip_tickers:
        assert shock_for(ticker, shocks) == pytest.approx(-0.25), f"Expected -0.25 for {ticker}"

    assert stress(pd.Series({"SNPS": 1.0}), shocks) == pytest.approx(-0.25)

    non_chip_software = ["MSFT", "ADBE", "CRM", "PLTR", "PANW", "CRWD", "NOW", "WDAY", "INTU", "ADSK"]
    for ticker in non_chip_software:
        assert shock_for(ticker, shocks) == pytest.approx(0.0), f"Expected 0.0 for {ticker}"


def test_chip_selloff_covers_dynamically_registered_semiconductor_ticker(monkeypatch):
    fake_ticker = "CDNS_TEST"
    monkeypatch.delitem(SECTORS, fake_ticker, raising=False)
    monkeypatch.delitem(GROUPS, fake_ticker, raising=False)

    class _DummyTicker:
        info = {"sector": "Technology", "industry": "Semiconductors"}

    fake_yf = types.SimpleNamespace(Ticker=lambda _t: _DummyTicker())
    monkeypatch.setitem(sys.modules, "yfinance", fake_yf)

    sector, group = classify_and_register_ticker(fake_ticker)
    assert sector == "Semiconductors"
    assert group == "AI & Semiconductors"
    assert shock_for(fake_ticker, SCENARIOS["Chip selloff (semis fall 25%)"]) == pytest.approx(-0.25)


def test_broad_selloff_covers_slv_and_gld():
    shocks = SCENARIOS["Broad selloff"]
    gld_shock = shock_for("GLD", shocks)
    slv_shock = shock_for("SLV", shocks)

    assert gld_shock == pytest.approx(0.03)
    assert slv_shock != 0.0
    assert slv_shock == pytest.approx(0.03)
    assert stress(pd.Series({"SLV": 1.0}), shocks) == pytest.approx(0.03)


def test_broad_selloff_covers_snps_and_unrelated_scenarios_stay_zero():
    assert shock_for("SNPS", SCENARIOS["Broad selloff"]) == pytest.approx(-0.15)
    assert shock_for("SNPS", SCENARIOS["Big Tech falls 20%"]) == pytest.approx(0.0)
    assert shock_for("SNPS", SCENARIOS["NVDA falls 15%"]) == pytest.approx(0.0)
    assert shock_for("SNPS", SCENARIOS["Crypto crash 40%"]) == pytest.approx(0.0)

    assert shock_for("SLV", SCENARIOS["Big Tech falls 20%"]) == pytest.approx(0.0)
    assert shock_for("SLV", SCENARIOS["Chip selloff (semis fall 25%)"]) == pytest.approx(0.0)
    assert shock_for("SLV", SCENARIOS["NVDA falls 15%"]) == pytest.approx(0.0)
    assert shock_for("SLV", SCENARIOS["Crypto crash 40%"]) == pytest.approx(0.0)


def test_stress_mixed_portfolios_with_snps_and_slv():
    w_chip_mix = pd.Series({"SNPS": 0.5, "MSFT": 0.5})
    assert stress(w_chip_mix, SCENARIOS["Chip selloff (semis fall 25%)"]) == pytest.approx(-0.125)
    assert stress(w_chip_mix, SCENARIOS["Broad selloff"]) == pytest.approx(-0.15)

    w_commodity_mix = pd.Series({"SLV": 0.5, "NVDA": 0.5})
    # 0.5 * 0.03 + 0.5 * (-0.15) = -0.06
    assert stress(w_commodity_mix, SCENARIOS["Broad selloff"]) == pytest.approx(-0.06)


def test_shock_for_precedence_ticker_over_sector_over_group():
    shocks = {
        "SNPS": -0.35,
        "Software & Semiconductors": -0.25,
        "Software & Cybersecurity": -0.15,
    }
    assert shock_for("SNPS", shocks) == pytest.approx(-0.35)
    assert shock_for("ADBE", shocks) == pytest.approx(-0.15)


def test_api_risk_snps_and_slv_stress_responses(monkeypatch):
    idx = pd.bdate_range("2025-01-01", periods=90)
    rng = np.random.default_rng(42)
    frame = pd.DataFrame({
        "SNPS": 450 * (1 + rng.normal(0.0005, 0.015, len(idx))).cumprod(),
        "SLV": 28 * (1 + rng.normal(0.0003, 0.012, len(idx))).cumprod(),
    }, index=idx)
    monkeypatch.setattr(api_module, "load_prices", lambda tickers, period="2y": frame[list(tickers)])

    res_snps = client.post("/risk", json={"weights": {"SNPS": 100}})
    assert res_snps.status_code == 200
    stress_snps = res_snps.json()["stress"]
    assert stress_snps["Chip selloff (semis fall 25%)"] == pytest.approx(-0.25)
    assert stress_snps["Broad selloff"] == pytest.approx(-0.15)

    res_slv = client.post("/risk", json={"weights": {"SLV": 100}})
    assert res_slv.status_code == 200
    stress_slv = res_slv.json()["stress"]
    assert stress_slv["Broad selloff"] == pytest.approx(0.03)
    assert stress_slv["Chip selloff (semis fall 25%)"] == pytest.approx(0.0)
