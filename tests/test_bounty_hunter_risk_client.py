import json
import pytest
from unittest.mock import patch, MagicMock
from scripts.bounty_hunter_risk_client import (
    AurenRiskClient,
    AurenValidationError,
    AurenAPIError,
    parse_weights_arg,
)


def test_parse_weights_arg_json():
    w = parse_weights_arg('{"NVDA": 50, "MSFT": 50}')
    assert w == {"NVDA": 50.0, "MSFT": 50.0}


def test_parse_weights_arg_colon_syntax():
    w = parse_weights_arg("NVDA:40, MSFT:30, GOOGL:30")
    assert w == {"NVDA": 40.0, "MSFT": 30.0, "GOOGL": 30.0}


def test_parse_weights_invalid_syntax():
    with pytest.raises(ValueError, match="Invalid weight format"):
        parse_weights_arg("INVALID_FORMAT")


def test_validation_empty_weights():
    client = AurenRiskClient()
    with pytest.raises(AurenValidationError, match="cannot be empty"):
        client.analyze_portfolio({})


def test_validation_negative_weight():
    client = AurenRiskClient()
    with pytest.raises(AurenValidationError, match="strictly positive"):
        client.analyze_portfolio({"NVDA": -10, "MSFT": 50})


def test_format_terminal_report():
    sample_data = {
        "score": 45,
        "level": "Medium",
        "volatility": 0.22,
        "max_drawdown": -0.15,
        "concentration": {
            "top_asset": "NVDA",
            "top_weight": 0.40,
            "effective_assets": 3.2,
        },
        "reasons": ["Largest holding is 40% (over 30%)"],
        "stress": {
            "Big Tech falls 20%": -0.08,
            "Crypto drops 30%": -0.03,
        },
        "disclaimer": "Analytics only, not investment advice.",
    }
    report = AurenRiskClient.format_terminal_report(sample_data)
    assert "AUREN RISK INTELLIGENCE REPORT" in report
    assert "Risk Score : 45 / 100" in report
    assert "[MEDIUM]" in report
    assert "Largest holding is 40%" in report
    assert "Big Tech falls 20%" in report


def test_analyze_portfolio_mocked_success():
    client = AurenRiskClient(base_url="http://mocked-auren.local")
    mock_payload = {
        "score": 35,
        "level": "Medium",
        "reasons": [],
        "concentration": {"top_asset": "MSFT", "top_weight": 0.35, "effective_assets": 3.0},
        "volatility": 0.18,
        "max_drawdown": -0.12,
        "sector_exposure": {"Software": 0.6, "Semiconductors": 0.4},
        "correlated_pairs": [],
        "stress": {},
        "disclaimer": "Analytics only, not investment advice.",
    }

    mock_resp = MagicMock()
    mock_resp.getcode.return_value = 200
    mock_resp.read.return_value = json.dumps(mock_payload).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = client.analyze_portfolio({"MSFT": 60, "NVDA": 40})
        assert res["score"] == 35
        assert res["level"] == "Medium"
        assert res["volatility"] == 0.18


def test_analyze_portfolio_incomplete_response_raises_error():
    client = AurenRiskClient(base_url="http://mocked-auren.local")
    incomplete_payload = {"score": 35}  # Missing required fields

    mock_resp = MagicMock()
    mock_resp.getcode.return_value = 200
    mock_resp.read.return_value = json.dumps(incomplete_payload).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        with pytest.raises(AurenAPIError, match="Incomplete API response contract"):
            client.analyze_portfolio({"MSFT": 50, "NVDA": 50})
