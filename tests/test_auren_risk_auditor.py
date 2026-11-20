import pytest
from scripts.auren_risk_auditor import audit_portfolio, AurenAuditError


def test_audit_offline_mock(monkeypatch):
    mock_response = {
        "concentration": {
            "top_asset": "NVDA",
            "top_weight": 0.4,
            "top3_weight": 0.9,
            "hhi": 0.29,
            "effective_assets": 3.45,
        },
        "score": {
            "score": 35,
            "level": "Medium",
            "hits": [(20, "Largest holding is 40% (over 30%)")],
        },
        "metrics": {
            "annualized_volatility": 0.38,
            "max_drawdown": -0.32,
        },
        "scenarios": {
            "Big Tech falls 20%": -0.18,
        },
    }

    import scripts.auren_risk_auditor as auditor
    monkeypatch.setattr(auditor, "query_risk_api", lambda w, base_url: mock_response)

    res = audit_portfolio({"NVDA": 40.0, "MSFT": 30.0, "GOOGL": 20.0, "BTC-USD": 10.0})
    assert res["status"] == "PASS"
    assert res["score"] == 35
    assert res["level"] == "Medium"
    assert res["hhi"] == 0.29
    assert res["top_asset"] == "NVDA"
