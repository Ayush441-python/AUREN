import streamlit as st


def test_stress_progress_column_format():
    """Verify that the ProgressColumn format for scenario stress tests uses 'percent'

    to correctly scale fractional impacts (e.g. -0.20 as -20% instead of -0.2%).
    """
    col = st.column_config.ProgressColumn(
        "Impact %", min_value=-0.50, max_value=0.10, format="percent"
    )
    assert col["type_config"]["type"] == "progress"
    assert col["type_config"]["format"] == "percent"
    assert col["type_config"]["min_value"] == -0.50
    assert col["type_config"]["max_value"] == 0.10
