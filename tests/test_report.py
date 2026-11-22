"""Regression tests for the AI-report hallucination guard (issue #110)."""
import json

from engine.report import unverified_numbers


def _metrics(vol=0.25, score=62):
    return {"risk_score": score, "volatility_annualised": vol,
            "max_drawdown": -0.18, "top_weight": 0.40}


def test_report_checked_against_its_own_snapshot():
    snapshot = _metrics()
    report = "Risk score is 62 with volatility of 25% and a max drawdown of -18%."
    # Guard run against the snapshot the report was generated from: clean.
    assert unverified_numbers(report, snapshot) == []
    # Same report against different (current) metrics flags the stale figures.
    assert unverified_numbers(report, _metrics(vol=0.41, score=80)) != []


def test_snapshot_roundtrip_via_metrics_json():
    # app.py stores metrics_json = json.dumps(metrics, ...) in session state;
    # the guard must work on the parsed snapshot, not the live metrics dict.
    metrics = _metrics()
    snapshot = json.loads(json.dumps(metrics, sort_keys=True, default=str))
    report = "Volatility is 25% and drawdown is -18%."
    assert unverified_numbers(report, snapshot) == []
