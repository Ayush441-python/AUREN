"""Comprehensive unit and integration tests for OpenBot Risk Sentinel client."""

import io
import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api import app
from scripts.openbot_risk_sentinel import (
    AurenAPIError,
    AurenConnectionError,
    AurenError,
    AurenRiskClient,
    AurenValidationError,
    main,
    run_demo,
)


@pytest.fixture
def sample_risk_response():
    """Mock contract-compliant AUREN Risk API response."""
    return {
        "score": 62,
        "level": "HIGH",
        "reasons": ["Largest holding is 40% (over 30%)", "Behaves like only 2.7 assets"],
        "concentration": {
            "effective_n": 2.7,
            "top_pct": 0.40,
            "top_ticker": "NVDA",
            "herfindahl": 0.37,
        },
        "volatility": 0.285,
        "max_drawdown": -0.245,
        "sector_exposure": {
            "Semiconductors": 0.40,
            "Software": 0.30,
            "Internet & AI": 0.20,
            "Crypto": 0.10,
        },
        "correlated_pairs": [("NVDA", "MSFT", 0.74)],
        "stress": {
            "Big Tech falls 20%": -0.165,
            "Crypto drops 30%": -0.030,
        },
        "disclaimer": "Analytics only, not investment advice.",
    }


# ==============================================================================
# Weight Parsing & Sanitization Tests
# ==============================================================================

def test_parse_weights_from_json():
    raw = '{"NVDA": 40.0, "msft": 30, "googl": 20, "eth-usd": 10}'
    parsed = AurenRiskClient.parse_weights(raw)
    assert parsed == {"NVDA": 40.0, "MSFT": 30.0, "GOOGL": 20.0, "ETH-USD": 10.0}


def test_parse_weights_from_delimited_string():
    raw = "nvda:40, msft=30, googl:20, eth-usd:10"
    parsed = AurenRiskClient.parse_weights(raw)
    assert parsed == {"NVDA": 40.0, "MSFT": 30.0, "GOOGL": 20.0, "ETH-USD": 10.0}


def test_parse_weights_empty_raises_validation_error():
    with pytest.raises(AurenValidationError, match="Portfolio input cannot be empty"):
        AurenRiskClient.parse_weights("   ")


def test_parse_weights_invalid_json():
    with pytest.raises(AurenValidationError, match="Invalid JSON format"):
        AurenRiskClient.parse_weights('{"NVDA": 40,')


def test_parse_weights_invalid_delimiter():
    with pytest.raises(AurenValidationError, match="Invalid token"):
        AurenRiskClient.parse_weights("NVDA-40,MSFT-60")


def test_parse_weights_non_numeric():
    with pytest.raises(AurenValidationError, match="Invalid numeric weight"):
        AurenRiskClient.parse_weights("NVDA:abc,MSFT:30")


def test_parse_weights_zero_or_negative_rejected():
    with pytest.raises(AurenValidationError, match="must be strictly positive"):
        AurenRiskClient.parse_weights("NVDA:0,MSFT:50")

    with pytest.raises(AurenValidationError, match="must be strictly positive"):
        AurenRiskClient.parse_weights("NVDA:-10,MSFT:50")


# ==============================================================================
# HTTP Client & Contract Verification Tests
# ==============================================================================

def test_query_risk_success(sample_risk_response):
    client = AurenRiskClient(base_url="http://mocked-api:8000")
    response_bytes = json.dumps(sample_risk_response).encode("utf-8")

    mock_resp = MagicMock()
    mock_resp.read.return_value = response_bytes
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        result = client.query_risk({"NVDA": 40.0, "MSFT": 60.0})
        assert result["score"] == 62
        assert result["level"] == "HIGH"
        assert result["disclaimer"] == "Analytics only, not investment advice."
        mock_urlopen.assert_called_once()


def test_query_risk_missing_contract_field(sample_risk_response):
    client = AurenRiskClient(base_url="http://mocked-api:8000")
    del sample_risk_response["stress"]  # remove a required field
    response_bytes = json.dumps(sample_risk_response).encode("utf-8")

    mock_resp = MagicMock()
    mock_resp.read.return_value = response_bytes
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        with pytest.raises(AurenAPIError, match="missing contract fields"):
            client.query_risk({"NVDA": 50.0, "MSFT": 50.0})


def test_query_risk_http_400_validation_error():
    client = AurenRiskClient(base_url="http://mocked-api:8000")
    error_payload = json.dumps({"detail": "Unsupported tickers: ['UNKNOWN']"}).encode("utf-8")

    mock_http_err = urllib.error.HTTPError(
        url="http://mocked-api:8000/risk",
        code=400,
        msg="Bad Request",
        hdrs=None,
        fp=io.BytesIO(error_payload),
    )

    with patch("urllib.request.urlopen", side_effect=mock_http_err):
        with pytest.raises(AurenValidationError, match="Unsupported tickers"):
            client.query_risk({"UNKNOWN": 100.0})


def test_query_risk_http_500_api_error():
    client = AurenRiskClient(base_url="http://mocked-api:8000")
    error_payload = json.dumps({"detail": "Failed to load historical price series"}).encode("utf-8")

    mock_http_err = urllib.error.HTTPError(
        url="http://mocked-api:8000/risk",
        code=500,
        msg="Internal Server Error",
        hdrs=None,
        fp=io.BytesIO(error_payload),
    )

    with patch("urllib.request.urlopen", side_effect=mock_http_err):
        with pytest.raises(AurenAPIError, match="AUREN Server Error \\(HTTP 500\\)"):
            client.query_risk({"NVDA": 100.0})


def test_query_risk_connection_error():
    client = AurenRiskClient(base_url="http://unreachable-host:9999")
    mock_url_err = urllib.error.URLError("Connection refused")

    with patch("urllib.request.urlopen", side_effect=mock_url_err):
        with pytest.raises(AurenConnectionError, match="Cannot connect to AUREN API"):
            client.query_risk({"NVDA": 100.0})


# ==============================================================================
# Dashboard Formatter & Demo Tests
# ==============================================================================

def test_render_dashboard(sample_risk_response):
    weights = {"NVDA": 40.0, "MSFT": 30.0, "GOOGL": 20.0, "ETH-USD": 10.0}
    card = AurenRiskClient.render_dashboard(sample_risk_response, weights=weights)

    assert "AUREN RISK INTELLIGENCE REPORT" in card
    assert "Risk Score   :  62 / 100" in card
    assert "Level: [HIGH]" in card
    assert "Volatility   : 28.5% / yr" in card
    assert "Max Drawdown      : -24.5%" in card
    assert "Big Tech falls 20%" in card
    assert "Analytics only, not investment advice." in card
    assert "NVDA" in card


def test_run_demo(sample_risk_response, capsys):
    client = AurenRiskClient()
    with patch.object(client, "query_risk", return_value=sample_risk_response):
        ret = run_demo(client)
        assert ret == 0

    captured = capsys.readouterr()
    assert "LAUNCHING AUREN RISK SENTINEL MULTI-PORTFOLIO INTEGRATION DEMO" in captured.out
    assert "Balanced Multi-Asset Core" in captured.out
    assert "Demo completed: 3/3 portfolios evaluated." in captured.out


# ==============================================================================
# CLI Entry Point & Flag Tests
# ==============================================================================

def test_main_cli_weights_json_mode(sample_risk_response, capsys):
    with patch("sys.argv", ["openbot_risk_sentinel.py", "--weights", "NVDA:50,MSFT:50", "--json"]):
        with patch.object(AurenRiskClient, "query_risk", return_value=sample_risk_response):
            exit_code = main()
            assert exit_code == 0

    captured = capsys.readouterr()
    parsed_json = json.loads(captured.out)
    assert parsed_json["score"] == 62


def test_main_cli_export(sample_risk_response, tmp_path):
    export_file = tmp_path / "exported_risk.json"
    with patch(
        "sys.argv",
        [
            "openbot_risk_sentinel.py",
            "--weights",
            "NVDA:50,MSFT:50",
            "--export",
            str(export_file),
        ],
    ):
        with patch.object(AurenRiskClient, "query_risk", return_value=sample_risk_response):
            exit_code = main()
            assert exit_code == 0

    assert export_file.exists()
    saved_data = json.loads(export_file.read_text(encoding="utf-8"))
    assert saved_data["score"] == 62


# ==============================================================================
# Direct FastAPI TestClient Live Contract Integration
# ==============================================================================

def test_live_fastapi_contract_compatibility():
    """Verify that AurenRiskClient expectations exactly match FastAPI app.py contract."""
    client = TestClient(app)
    response = client.post("/risk", json={"weights": {"NVDA": 40.0, "MSFT": 30.0, "COST": 30.0}})
    assert response.status_code == 200

    data = response.json()
    AurenRiskClient._verify_contract(data)

    assert 0 <= data["score"] <= 100
    assert data["level"].upper() in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    assert isinstance(data["stress"], dict)
    assert len(data["stress"]) > 0
