from unittest.mock import patch
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)


def test_api_risk_correlated_pairs_precision_auditable():
    mock_corr = pd.DataFrame(
        [[1.0, 0.704, 0.704], [0.704, 1.0, 0.0], [0.704, 0.0, 1.0]],
        index=["NVDA", "MSFT", "GOOGL"],
        columns=["NVDA", "MSFT", "GOOGL"],
    )
    with patch("api.correlation", return_value=mock_corr):
        res = client.post(
            "/risk",
            json={"weights": {"NVDA": 20, "MSFT": 40, "GOOGL": 40}},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["correlated_pairs"] == [
            ["NVDA", "MSFT", 0.704],
            ["NVDA", "GOOGL", 0.704],
        ]
        assert "2 pairs of assets move closely together" in data["reasons"]
        assert all(pair[2] > 0.70 for pair in data["correlated_pairs"])


def test_api_risk_correlated_pairs_boundary_700_not_included():
    mock_corr = pd.DataFrame(
        [[1.0, 0.700, 0.700], [0.700, 1.0, 0.0], [0.700, 0.0, 1.0]],
        index=["NVDA", "MSFT", "GOOGL"],
        columns=["NVDA", "MSFT", "GOOGL"],
    )
    with patch("api.correlation", return_value=mock_corr):
        res = client.post(
            "/risk",
            json={"weights": {"NVDA": 20, "MSFT": 40, "GOOGL": 40}},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["correlated_pairs"] == []
        assert "2 pairs of assets move closely together" not in data["reasons"]
