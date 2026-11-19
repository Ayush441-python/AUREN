import json

from engine.report import unverified_numbers


def test_guard_validates_against_generation_snapshot():
    # Portfolio A metrics
    metrics_a = {
        "risk_score": 65,
        "volatility_annualised": 0.2965,
        "max_drawdown": -0.3083,
        "effective_assets": 3.33,
    }

    # Portfolio B metrics
    metrics_b = {
        "risk_score": 0,
        "volatility_annualised": 0.1839,
        "max_drawdown": -0.1837,
        "effective_assets": 5.56,
    }

    # Report generated for Portfolio A
    report_a = (
        "Your risk score is 65 (High). Annual volatility is 29.6% "
        "and the worst fall was 30.8%. Effective assets: 3.33."
    )

    # Session state stored as tuple (metrics_json, text)
    rep = (json.dumps(metrics_a), report_a)

    # Validating against live metrics_b falsely flags real figures as hallucinations
    bad_live = unverified_numbers(rep[1], metrics_b)
    assert 65.0 in bad_live

    # Validating against generation snapshot correctly passes without false positives
    snapshot = json.loads(rep[0])
    bad_snapshot = unverified_numbers(rep[1], snapshot)
    assert bad_snapshot == []
