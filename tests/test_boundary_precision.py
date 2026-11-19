from unittest.mock import patch

import api
import engine.data as d
import pandas as pd
import pytest
from engine.metrics import concentration
from engine.score import risk_score
from fastapi.testclient import TestClient


def test_concentration_exact_30_percent_boundary():
    # Fractions summing to 1.0 (with IEEE 754 precision skew: 0.9999999999999999)
    w_frac = pd.Series([0.3, 0.275, 0.2, 0.225], index=["GLD", "COST", "JPM", "XOM"])
    w_frac = w_frac / w_frac.sum()

    conc = concentration(w_frac)
    assert conc["top_weight"] == pytest.approx(0.30)
    assert conc["top_weight"] <= 0.30  # Exact 30% is not strictly over 30%


def test_api_risk_identical_scores_regardless_of_input_units():
    p = pd.read_csv(d.CACHE, index_col=0, parse_dates=True)
    with patch.object(api, "load_prices", side_effect=lambda k: p[k]), TestClient(api.app) as c:
        # Whole percentages [30, 27.5, 20, 22.5]
        r1 = c.post(
            "/risk",
            json={"weights": {"GLD": 30, "COST": 27.5, "JPM": 20, "XOM": 22.5}},
        ).json()

        # Decimal fractions [0.3, 0.275, 0.2, 0.225]
        r2 = c.post(
            "/risk",
            json={"weights": {"GLD": 0.3, "COST": 0.275, "JPM": 0.2, "XOM": 0.225}},
        ).json()

        assert r1["score"] == 15
        assert r1["level"] == "Low"
        assert r2["score"] == 15
        assert r2["level"] == "Low"
        assert r1["concentration"]["top_weight"] == pytest.approx(0.30)
        assert r2["concentration"]["top_weight"] == pytest.approx(0.30)


def test_boundary_controls():
    conc_30 = {"top_weight": 0.30, "effective_assets": 10}
    score_30, _, _ = risk_score(conc_30, 0.10, -0.05, [], 0.20)
    assert score_30 == 0

    conc_30_01 = {"top_weight": 0.3001, "effective_assets": 10}
    score_30_01, _, _ = risk_score(conc_30_01, 0.10, -0.05, [], 0.20)
    assert score_30_01 == 20

    conc_29_99 = {"top_weight": 0.2999, "effective_assets": 10}
    score_29_99, _, _ = risk_score(conc_29_99, 0.10, -0.05, [], 0.20)
    assert score_29_99 == 0
