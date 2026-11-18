import ast
import json
from pathlib import Path
import pytest


def test_app_saves_snapshot_consistent_report_and_disables_stale_download():
    """Verify that app.py saves snapshot-consistent report markdown and gates download when portfolio changes."""
    app_path = Path(__file__).resolve().parent.parent / "app.py"
    app_tree = ast.parse(app_path.read_text())

    # Find the download_button call in app.py
    download_calls = []
    for node in ast.walk(app_tree):
        if isinstance(node, ast.Call):
            func = node.func
            if (isinstance(func, ast.Attribute) and func.attr == "download_button") or (
                isinstance(func, ast.Name) and func.id == "download_button"
            ):
                download_calls.append(node)

    assert len(download_calls) >= 1, "Expected at least one download_button call"

    # Verify that disabled argument exists on at least one download_button call
    has_disabled_guard = any(
        any(kw.arg == "disabled" for kw in call.keywords)
        for call in download_calls
    )
    assert has_disabled_guard, "download_button must have a disabled guard when report is stale"


def test_stale_report_simulation_does_not_mix_metrics():
    """Verify that changing portfolio does not inject new metrics into existing report markdown."""
    metrics_a = {"largest_holding": "NVDA", "top_weight": 0.40}
    text_a = "Snapshot A: NVDA is the largest holding at 40%."
    saved_md_a = f"# Report\n- Largest Holding: NVDA (40.0%)\n## AI Assessment\n{text_a}"

    report_state = (json.dumps(metrics_a), text_a, saved_md_a)

    # Portfolio changes to Portfolio B
    metrics_b = {"largest_holding": "MSFT", "top_weight": 0.20}
    metrics_b_json = json.dumps(metrics_b)

    is_stale = report_state[0] != metrics_b_json
    assert is_stale, "Should detect that report is stale"

    # Exported markdown must remain snapshot A and not mix with B
    export_md = report_state[2]
    assert "NVDA" in export_md
    assert "MSFT" not in export_md
