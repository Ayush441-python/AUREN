import json
import pathlib
import re

import pandas as pd
import pytest

from engine.metrics import concentration, high_pairs, sector_exposure
from engine.score import risk_score
from engine.stress import SCENARIOS, stress

MOCK_TS = pathlib.Path(__file__).resolve().parent.parent / "web" / "src" / "lib" / "mock.ts"


def _load_base_portfolio_analysis() -> dict:
    src = MOCK_TS.read_text(encoding="utf-8")
    match = re.search(
        r"export\s+const\s+BASE_PORTFOLIO_ANALYSIS\s*:\s*RiskAnalysis\s*=\s*(\{.*?\});",
        src,
        re.DOTALL,
    )
    assert match is not None, "Could not locate BASE_PORTFOLIO_ANALYSIS in web/src/lib/mock.ts"
    literal = match.group(1)
    # Quote unquoted JS object keys and strip trailing commas so standard json.loads parses it.
    json_like = re.sub(
        r'([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*:)',
        r'\1"\2"\3',
        literal,
    )
    json_like = re.sub(r",(\s*[}\]])", r"\1", json_like)
    return json.loads(json_like)


def test_reference_fixture_weights_and_concentration_match_engine():
    fixture = _load_base_portfolio_analysis()
    weights = pd.Series(fixture["normalized_weights"], dtype=float)
    assert weights.sum() == pytest.approx(1.0)

    expected_conc = concentration(weights)
    actual_conc = fixture["concentration"]

    assert actual_conc["top_asset"] == expected_conc["top_asset"]
    assert actual_conc["top_weight"] == pytest.approx(round(expected_conc["top_weight"], 4))
    assert actual_conc["top3_weight"] == pytest.approx(round(expected_conc["top3_weight"], 4))
    assert actual_conc["hhi"] == pytest.approx(round(expected_conc["hhi"], 4))
    assert actual_conc["effective_assets"] == pytest.approx(round(expected_conc["effective_assets"], 2))


def test_reference_fixture_correlated_pairs_match_engine():
    fixture = _load_base_portfolio_analysis()
    matrix = fixture["correlation_matrix"]
    corr_df = pd.DataFrame(matrix["data"], index=matrix["columns"], columns=matrix["columns"])

    expected_pairs = [list(pair) for pair in high_pairs(corr_df)]
    assert fixture["correlated_pairs"] == expected_pairs
    assert len(fixture["correlated_pairs"]) == 2
    assert all(pair[2] > 0.70 for pair in fixture["correlated_pairs"])


def test_reference_fixture_sector_exposure_matches_engine():
    fixture = _load_base_portfolio_analysis()
    weights = pd.Series(fixture["normalized_weights"], dtype=float)
    expected_exposure = {k: round(float(v), 4) for k, v in sector_exposure(weights).to_dict().items()}
    assert fixture["sector_exposure"] == expected_exposure


def test_reference_fixture_score_tier_hits_and_reasons_match_engine():
    fixture = _load_base_portfolio_analysis()
    weights = pd.Series(fixture["normalized_weights"], dtype=float)
    matrix = fixture["correlation_matrix"]
    corr_df = pd.DataFrame(matrix["data"], index=matrix["columns"], columns=matrix["columns"])

    conc = concentration(weights)
    pairs = high_pairs(corr_df)
    exposure = sector_exposure(weights)
    max_sec_exp = float(exposure.max())

    expected_score, expected_level, expected_hits = risk_score(
        conc,
        fixture["volatility"],
        fixture["max_drawdown"],
        pairs,
        max_sec_exp,
    )

    assert fixture["score"] == expected_score == 65
    assert fixture["level"] == expected_level == "High"
    assert fixture["hits"] == [[pts, why] for pts, why in expected_hits]
    assert sum(pts for pts, _ in fixture["hits"]) == fixture["score"]
    assert fixture["reasons"] == [why for _, why in expected_hits]


def test_reference_fixture_stress_scenarios_match_engine():
    fixture = _load_base_portfolio_analysis()
    weights = pd.Series(fixture["normalized_weights"], dtype=float)
    expected_stress = {name: round(stress(weights, shocks), 4) for name, shocks in SCENARIOS.items()}
    assert fixture["stress"] == expected_stress
