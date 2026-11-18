"""Dashboard regressions using Streamlit's real widget/session runtime."""
import json
from pathlib import Path

import pytest
from streamlit.dataframe_util import convert_arrow_bytes_to_pandas_df
from streamlit.testing.v1 import AppTest


APP = Path(__file__).resolve().parents[1] / "app.py"


def whatif_editor(at):
    return next(
        element for element in at.get("dataframe")
        if (getattr(element, "key", None) or "").startswith("pfb_")
    )


def edit_whatif(at, *, edited_rows, added_rows=(), deleted_rows=()):
    # AppTest does not yet expose a data_editor.set_value(). Feed the real
    # editor its frontend JSON state through the test runner's widget states.
    states = at._tree.get_widget_states()
    states.widgets.add(
        id=whatif_editor(at).proto.id,
        string_value=json.dumps({
            "edited_rows": edited_rows,
            "added_rows": list(added_rows),
            "deleted_rows": list(deleted_rows),
        }),
    )
    at._run(states)
    assert not at.exception


def normalize_whatif(at):
    next(
        button for button in at.button
        if button.label == "Normalize What-if to 100%"
    ).click().run()
    assert not at.exception
    return convert_arrow_bytes_to_pandas_df(whatif_editor(at).proto.arrow_data.data)


@pytest.fixture
def dashboard(monkeypatch):
    # Exercise the actual app and its committed price/volume cache offline.
    # Only the Yahoo download is disabled; widgets and calculations are real.
    monkeypatch.setattr("engine.data._download", lambda *args: None)
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not at.exception
    return at


def test_normalize_whatif_survives_rerun_and_preserves_current_portfolio(dashboard):
    at = dashboard
    current = at.session_state["pf_df"].copy(deep=True)
    edit_whatif(at, edited_rows={"0": {"weight": 20.0}})
    normalized = normalize_whatif(at)
    assert normalized["weight"].tolist() == pytest.approx([25, 37.5, 25, 12.5])
    assert normalized["weight"].sum() == pytest.approx(100)
    at.run()
    assert not at.exception
    rerun_frame = convert_arrow_bytes_to_pandas_df(whatif_editor(at).proto.arrow_data.data)
    assert rerun_frame.equals(normalized)
    assert at.session_state["pf_df"].equals(current)
    assert not any("What-if weights must" in warning.value for warning in at.warning)


def test_normalize_whatif_keeps_dynamic_rows_and_exact_total(dashboard):
    at = dashboard
    edit_whatif(
        at,
        edited_rows={
            "0": {"ticker": "COST", "weight": 10.0},
            "1": {"weight": 10.0},
        },
        deleted_rows=[2, 3],
        added_rows=[{"ticker": "JPM", "weight": 10.0}],
    )
    normalized = normalize_whatif(at)
    assert normalized["ticker"].tolist() == ["COST", "MSFT", "JPM"]
    assert normalized["weight"].tolist() == pytest.approx([100 / 3] * 3)
    assert abs(normalized["weight"].sum() - 100) <= 0.01

    # Normalize again after another edit to catch stale widget edit replay.
    edit_whatif(at, edited_rows={"0": {"weight": 10.0}})
    normalized_again = normalize_whatif(at)
    assert normalized_again["ticker"].tolist() == ["COST", "MSFT", "JPM"]
    assert normalized_again["weight"].tolist() == pytest.approx([300 / 23, 1000 / 23, 1000 / 23])
    assert abs(normalized_again["weight"].sum() - 100) <= 0.01
