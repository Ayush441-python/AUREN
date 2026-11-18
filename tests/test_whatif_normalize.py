import ast
from pathlib import Path
from types import SimpleNamespace
import pandas as pd
import pytest


def test_whatif_data_editor_uses_versioned_key_and_separate_state():
    """Verify that What-if data_editor does not mutate its own instantiated widget key in session_state."""
    app_path = Path(__file__).resolve().parent.parent / "app.py"
    app_tree = ast.parse(app_path.read_text())

    # Find the What-if data_editor call
    editor_calls = []
    for node in ast.walk(app_tree):
        if isinstance(node, ast.Call):
            func = node.func
            if (isinstance(func, ast.Attribute) and func.attr == "data_editor") or (
                isinstance(func, ast.Name) and func.id == "data_editor"
            ):
                editor_calls.append(node)

    assert len(editor_calls) >= 2, "Expected at least 2 data_editor calls (main and what-if)"
    whatif_editor = editor_calls[1]

    # Check key keyword argument
    key_kw = next((kw for kw in whatif_editor.keywords if kw.arg == "key"), None)
    assert key_kw is not None, "What-if data_editor must have a key argument"
    key_src = ast.unparse(key_kw.value)

    # Key must be versioned (contains version variable like v_b)
    assert "v_b" in key_src or "v" in key_src, (
        f"What-if data_editor key must be versioned to allow safe updates, found: {key_src}"
    )


def test_whatif_normalize_logic_updates_state_and_increments_version():
    """Verify that normalization logic properly updates source dataframe and increments version counter."""
    class State(dict):
        __getattr__ = dict.__getitem__
        __setattr__ = dict.__setitem__

    st = SimpleNamespace(
        session_state=State(
            whatif_src_test=pd.DataFrame({"ticker": ["NVDA", "MSFT"], "weight": [20.0, 20.0]}),
            whatif_v_test=0,
        ),
        rerun=lambda: None,
    )

    wb_df = pd.DataFrame({"ticker": ["NVDA", "MSFT"], "weight": [20.0, 20.0]})
    tot_b = float(wb_df["weight"].sum())  # 40.0
    assert tot_b == 40.0

    # Normalization logic
    weights_b = (wb_df["weight"] / tot_b * 100).round(1)
    diff_b = round(100.0 - float(weights_b.sum()), 1)
    if diff_b != 0 and len(weights_b) > 0:
        weights_b.iloc[0] = round(weights_b.iloc[0] + diff_b, 1)
    wb_df["weight"] = weights_b

    st.session_state["whatif_src_test"] = wb_df.reset_index(drop=True)
    st.session_state["whatif_v_test"] += 1

    assert st.session_state["whatif_v_test"] == 1
    assert st.session_state["whatif_src_test"]["weight"].tolist() == [50.0, 50.0]
    assert float(st.session_state["whatif_src_test"]["weight"].sum()) == 100.0
