"""
Unit tests for Auren Risk Client (Bounty Hunter Sentinel).
Tests input sanitization, error responses, contract validation, and report formatting.
"""

from __future__ import annotations

import io
import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from scripts.bounty_hunter_risk_client import (
    AurenAPIError,
    AurenClientError,
    AurenContractError,
    AurenRiskClient,
    export_json,
    format_report,
    sanitize_weights,
    validate_contract,
)


@pytest.fixture
def client() -> AurenRiskClient:
    return AurenRiskClient(base_url="http://localhost:8000")


@pytest.fixture
def sample_risk_data() -> dict:
    return {
        "score": 55,
        "level": "MEDIUM",
        "volatility": 0.284,
        "max_drawdown": -0.241,
        "concentration": {
            "top_asset": "NVDA",
            "top_weight": 0.35,
            "top3_weight": 0.85,
            "hhi": 0.29,
            "effective_assets": 3.4,
        },
        "reasons": [
            "Largest holding is 35% (over 30%)",
            "Behaves like only 3.4 assets",
        ],
        "stress": {
            "Big Tech falls 20%": -0.14,
            "Crypto drops 30%": -0.09,
        },
        "sector_exposure": {
            "Big Tech": 0.70,
            "Crypto": 0.30,
        },
        "correlated_pairs": [
            ("NVDA", "MSFT", 0.75),
        ],
        "disclaimer": "Analytics only, not investment advice.",
    }


# ---------------------------------------------------------------------------
# Test 1: Input Sanitization - Valid Formats
# ---------------------------------------------------------------------------
def test_input_sanitization_valid(client: AurenRiskClient) -> None:
    # 1. Comma-separated pairs
    res1 = client.sanitize_weights("NVDA:35,MSFT:35,ETH-USD:15,BTC-USD:15")
    assert res1 == {"NVDA": 35.0, "MSFT": 35.0, "ETH-USD": 15.0, "BTC-USD": 15.0}

    # 2. Lowercase symbols with irregular whitespace
    res2 = client.sanitize_weights("  nvda :  40 ,  msft : 60  ")
    assert res2 == {"NVDA": 40.0, "MSFT": 60.0}

    # 3. Equals delimiter
    res3 = client.sanitize_weights("NVDA=50, MSFT=50")
    assert res3 == {"NVDA": 50.0, "MSFT": 50.0}

    # 4. Semicolon delimiter & percentage signs
    res4 = client.sanitize_weights("NVDA: 40%; MSFT: 60%")
    assert res4 == {"NVDA": 40.0, "MSFT": 60.0}

    # 5. JSON string format
    res5 = client.sanitize_weights('{"NVDA": 70, "MSFT": 30}')
    assert res5 == {"NVDA": 70.0, "MSFT": 30.0}

    # 6. Dictionary input
    res6 = client.sanitize_weights({"nvda": 25, "aapl": "75"})
    assert res6 == {"NVDA": 25.0, "AAPL": 75.0}

    # 7. Mixed semicolon and comma
    res7 = client.sanitize_weights("NVDA: 40; MSFT: 30, ETH-USD: 30")
    assert res7 == {"NVDA": 40.0, "MSFT": 30.0, "ETH-USD": 30.0}


# ---------------------------------------------------------------------------
# Test 2: Input Sanitization - Invalid Inputs
# ---------------------------------------------------------------------------
def test_input_sanitization_invalid(client: AurenRiskClient) -> None:
    # Empty inputs
    with pytest.raises(ValueError, match="cannot be empty"):
        client.sanitize_weights("")

    with pytest.raises(ValueError, match="cannot be empty"):
        client.sanitize_weights({})

    with pytest.raises(ValueError, match="cannot be empty"):
        client.sanitize_weights("   ")

    # Non-numeric weights
    with pytest.raises(ValueError, match="Invalid numeric weight"):
        client.sanitize_weights("NVDA:abc,MSFT:20")

    # Boolean weight
    with pytest.raises(ValueError, match="Invalid numeric weight"):
        client.sanitize_weights({"NVDA": True, "MSFT": 50})

    # Negative weights
    with pytest.raises(ValueError, match="must be positive"):
        client.sanitize_weights("NVDA:-10,MSFT:50")

    # Zero weights
    with pytest.raises(ValueError, match="must be positive"):
        client.sanitize_weights("NVDA:0,MSFT:50")

    # Invalid token format without separator
    with pytest.raises(ValueError, match="Invalid weight token"):
        client.sanitize_weights("NVDA MSFT 50")

    # Missing ticker symbol
    with pytest.raises(ValueError, match="Ticker symbol cannot be empty"):
        client.sanitize_weights(":50,MSFT:50")

    # Invalid type
    with pytest.raises(TypeError, match="must be a dict or string"):
        client.sanitize_weights(12345)  # type: ignore


# ---------------------------------------------------------------------------
# Test 3: Error Responses - HTTP 400 Bad Request
# ---------------------------------------------------------------------------
def test_error_handling_http_400(client: AurenRiskClient) -> None:
    error_payload = json.dumps({
        "detail": "Unsupported tickers: ['SOL-USD']. Supported tickers: ['NVDA', 'MSFT']"
    }).encode("utf-8")

    http_error = urllib.error.HTTPError(
        url="http://localhost:8000/risk",
        code=400,
        msg="Bad Request",
        hdrs={},
        fp=io.BytesIO(error_payload),
    )

    with patch("urllib.request.urlopen", side_effect=http_error):
        with pytest.raises(AurenAPIError) as exc_info:
            client.assess_risk("NVDA:35,MSFT:35,ETH-USD:15,SOL-USD:15")

        assert exc_info.value.status_code == 400
        assert "Unsupported tickers" in exc_info.value.detail
        assert "SOL-USD" in exc_info.value.detail


# ---------------------------------------------------------------------------
# Test 4: Error Responses - HTTP 500 Internal Server Error
# ---------------------------------------------------------------------------
def test_error_handling_http_500(client: AurenRiskClient) -> None:
    error_payload = json.dumps({
        "detail": "Failed to load historical price series"
    }).encode("utf-8")

    http_error = urllib.error.HTTPError(
        url="http://localhost:8000/risk",
        code=500,
        msg="Internal Server Error",
        hdrs={},
        fp=io.BytesIO(error_payload),
    )

    with patch("urllib.request.urlopen", side_effect=http_error):
        with pytest.raises(AurenAPIError) as exc_info:
            client.assess_risk({"NVDA": 50, "MSFT": 50})

        assert exc_info.value.status_code == 500
        assert "Failed to load historical price series" in exc_info.value.detail


# ---------------------------------------------------------------------------
# Test 5: Contract Validation - Successful Verification
# ---------------------------------------------------------------------------
def test_contract_validation_success(client: AurenRiskClient, sample_risk_data: dict) -> None:
    assert client.validate_contract(sample_risk_data) is True
    assert validate_contract(sample_risk_data) is True


# ---------------------------------------------------------------------------
# Test 6: Contract Validation - Missing & Invalid Fields
# ---------------------------------------------------------------------------
def test_contract_validation_missing_fields(client: AurenRiskClient, sample_risk_data: dict) -> None:
    # Non-dict response
    with pytest.raises(AurenContractError, match="expected dict"):
        client.validate_contract(["not", "a", "dict"])

    # Test removing each required field individually
    required_fields = [
        "score",
        "level",
        "reasons",
        "concentration",
        "volatility",
        "max_drawdown",
        "sector_exposure",
        "stress",
    ]
    for field in required_fields:
        tampered = sample_risk_data.copy()
        del tampered[field]
        with pytest.raises((AurenContractError, ValueError), match="Missing required contract fields"):
            client.validate_contract(tampered)

    # Test invalid field type
    type_tampered = sample_risk_data.copy()
    type_tampered["score"] = "invalid_string_score"
    with pytest.raises(AurenContractError, match="'score' must be numeric"):
        client.validate_contract(type_tampered)

    bool_tampered = sample_risk_data.copy()
    bool_tampered["score"] = True
    with pytest.raises(AurenContractError, match="'score' must be numeric"):
        client.validate_contract(bool_tampered)


# ---------------------------------------------------------------------------
# Test 7: Terminal & Dashboard Reporting - Format Card
# ---------------------------------------------------------------------------
def test_report_formatting(client: AurenRiskClient, sample_risk_data: dict) -> None:
    expected_report = (
        "================================================================\n"
        "                 AUREN RISK INTELLIGENCE REPORT                 \n"
        "================================================================\n"
        "Risk Score : 55 / 100\n"
        "Risk Level : [MEDIUM]\n"
        "Volatility : 28.4% a year\n"
        "Max DD     : -24.1%\n"
        "Top Asset  : NVDA (35.0%)\n"
        "Eff. Assets: 3.4\n"
        "----------------------------------------------------------------\n"
        "FLAGGED RISK FACTORS:\n"
        "  * Largest holding is 35% (over 30%)\n"
        "  * Behaves like only 3.4 assets\n"
        "----------------------------------------------------------------\n"
        "STRESS SCENARIOS:\n"
        "  * Big Tech falls 20%             : -14.0%\n"
        "  * Crypto drops 30%               : -9.0%\n"
        "----------------------------------------------------------------\n"
        "Disclaimer: Analytics only, not investment advice.\n"
        "================================================================"
    )

    rendered = client.format_report(sample_risk_data)
    assert rendered == expected_report

    # Test fallback formatting when reasons or stress are empty
    empty_data = sample_risk_data.copy()
    empty_data["reasons"] = []
    empty_data["stress"] = {}
    rendered_empty = client.format_report(empty_data)
    assert "  * None detected" in rendered_empty
    assert "  * None evaluated" in rendered_empty


# ---------------------------------------------------------------------------
# Test 8: JSON Export - Serialization & File Output
# ---------------------------------------------------------------------------
def test_json_export(client: AurenRiskClient, sample_risk_data: dict, tmp_path) -> None:
    # String export
    json_str = client.export_json(sample_risk_data)
    parsed = json.loads(json_str)
    assert parsed["score"] == 55
    assert parsed["level"] == "MEDIUM"
    assert parsed["concentration"]["top_asset"] == "NVDA"

    # File export
    export_file = tmp_path / "auren_risk_report.json"
    client.export_json(sample_risk_data, filepath=str(export_file))

    assert export_file.exists()
    file_content = export_file.read_text(encoding="utf-8")
    file_parsed = json.loads(file_content)
    assert file_parsed["score"] == 55
    assert file_parsed["stress"]["Big Tech falls 20%"] == -0.14
