import ast
from pathlib import Path
from types import SimpleNamespace
import pandas as pd
import pytest


def setup_mock_environment():
    app_path = Path(__file__).resolve().parent.parent / "app.py"
    wallet_path = Path(__file__).resolve().parent.parent / "engine" / "wallet.py"

    app_tree = ast.parse(app_path.read_text())
    wallet_tree = ast.parse(wallet_path.read_text())

    def get_fn(tree, name):
        return next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)

    scope = {
        "pd": pd,
        "is_valid_address": lambda addr: True,
        "wallet_holdings": lambda *args: {
            "rows": [{"ticker": "COST", "value": 1000.0, "supported": True}],
            "n_tokens": 1,
        },
        "setting": lambda *args: None,
        "BASE_RPC": "unused",
        "SECTORS": {"COST": "Consumer Staples"},
    }

    # Load holdings_to_portfolio
    exec(compile(ast.Module([get_fn(wallet_tree, "holdings_to_portfolio")], type_ignores=[]), "upstream", "exec"), scope)

    # Load PRESETS dict
    preset_def = next(
        n for n in app_tree.body
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "PRESETS" for t in n.targets)
    )
    exec(compile(ast.Module([preset_def], type_ignores=[]), "upstream", "exec"), scope)

    # Load load_wallet function
    exec(compile(ast.Module([get_fn(app_tree, "load_wallet")], type_ignores=[]), "upstream", "exec"), scope)

    # Find preset check if statement
    preset_check = next(
        n for n in ast.walk(app_tree)
        if isinstance(n, ast.If) and "selected_preset != st.session_state.last_preset" in ast.unparse(n.test)
    )

    return scope, preset_check


def test_wallet_import_does_not_get_overwritten_by_default_preset():
    scope, preset_check = setup_mock_environment()

    class State(dict):
        __getattr__ = dict.__getitem__
        __setattr__ = dict.__setitem__

    st = SimpleNamespace(
        session_state=State(
            wallet_addr="0x1234567890123456789012345678901234567890",
            pf_v=0,
            preset_choice="Balanced Tech & Crypto (Default)",
            last_preset="Balanced Tech & Crypto (Default)",
        ),
        rerun=lambda: None,
    )
    scope["st"] = st

    # 1. Simulate wallet load
    scope["load_wallet"]()

    assert st.session_state.pf_df.ticker.tolist() == ["COST"]
    assert st.session_state.preset_choice == "Custom / Edited"
    assert st.session_state.last_preset == "Custom / Edited"
    assert st.session_state.wallet_msg[0] == "success"

    # 2. Simulate preset check evaluation during rerun
    scope["selected_preset"] = st.session_state.preset_choice
    exec(compile(ast.Module([preset_check], type_ignores=[]), "upstream", "exec"), scope)

    # Holdings must remain COST and not be overwritten by Balanced Tech & Crypto
    assert st.session_state.pf_df.ticker.tolist() == ["COST"]


def test_preset_changes_only_on_explicit_selection_change():
    scope, preset_check = setup_mock_environment()

    class State(dict):
        __getattr__ = dict.__getitem__
        __setattr__ = dict.__setitem__

    st = SimpleNamespace(
        session_state=State(
            wallet_addr="0x1234567890123456789012345678901234567890",
            pf_v=0,
            preset_choice="Custom / Edited",
            last_preset="Custom / Edited",
            pf_df=pd.DataFrame([{"ticker": "COST", "weight": 100.0}]),
        ),
        rerun=lambda: None,
    )
    scope["st"] = st

    # Same preset selected: no change
    scope["selected_preset"] = "Custom / Edited"
    exec(compile(ast.Module([preset_check], type_ignores=[]), "upstream", "exec"), scope)
    assert st.session_state.pf_df.ticker.tolist() == ["COST"]

    # Explicit change to another preset
    scope["selected_preset"] = "Magnificent 7 Tech Heavy"
    exec(compile(ast.Module([preset_check], type_ignores=[]), "upstream", "exec"), scope)

    assert st.session_state.last_preset == "Magnificent 7 Tech Heavy"
    assert "AAPL" in st.session_state.pf_df.ticker.tolist()


def test_app_renders_cleanly_via_apptest():
    from streamlit.testing.v1 import AppTest

    app_path = str(Path(__file__).resolve().parent.parent / "app.py")
    at = AppTest.from_file(app_path, default_timeout=15).run()
    assert len(at.exception) == 0, f"App execution raised: {at.exception}"
    assert at.sidebar.selectbox[0].value == "Balanced Tech & Crypto (Default)"

