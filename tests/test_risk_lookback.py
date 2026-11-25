import pandas as pd
import pytest
from fastapi.testclient import TestClient

import engine.data as market_data
from api import app


@pytest.mark.parametrize(("period", "first_date", "expected_status"), [
    ("2mo", "2025-12-29", 200),
    ("1mo", None, 422),
    ("ytd", "2026-01-01", 200),
    ("2y", "2025-02-28", 200),
    ("max", "2025-02-28", 200),
])
def test_risk_bounds_the_one_year_retry(monkeypatch, tmp_path, period, first_date, expected_status):
    dates = pd.bdate_range("2025-02-28", "2026-02-27")
    prices = pd.DataFrame({"NVDA": 100.0}, index=dates)
    prices.loc[dates[:60], "NVDA"] = 50.0
    attempts = []

    def download(field, tickers, download_period):
        attempts.append((field, tickers, download_period))
        return prices if download_period == "1y" else None

    monkeypatch.setattr(market_data, "CACHE", tmp_path / "missing.csv")
    monkeypatch.setattr(market_data, "_memo", {})
    monkeypatch.setattr(market_data, "_download", download)

    with TestClient(app) as client:
        response = client.post("/risk", json={"weights": {"NVDA": 100}, "period": period})

    assert attempts == [("Close", ["NVDA"], period), ("Close", ["NVDA"], "1y")]
    assert response.status_code == expected_status
    result = response.json()
    if expected_status == 422:
        assert "need at least 30 trading days" in result["detail"]
    else:
        assert result["dates"][0] == first_date
        assert result["dates"][-1] == "2026-02-27"
        if period in {"2mo", "ytd"}:
            assert result["volatility"] == 0.0
