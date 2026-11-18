import ast
from pathlib import Path
import plotly.graph_objects as go
import pytest


def test_allocation_chart_hovertemplate_uses_customdata():
    """Verify that Allocation chart in app.py uses customdata for dollar formatting instead of fractional value."""
    app_path = Path(__file__).resolve().parent.parent / "app.py"
    app_tree = ast.parse(app_path.read_text())

    # Find the go.Pie call in app.py
    pie_call = None
    for node in ast.walk(app_tree):
        if isinstance(node, ast.Call):
            # Checking if function is go.Pie
            func = node.func
            if (isinstance(func, ast.Attribute) and func.attr == "Pie") or (
                isinstance(func, ast.Name) and func.id == "Pie"
            ):
                pie_call = node
                break

    assert pie_call is not None, "Could not find go.Pie call in app.py"

    # Extract hovertemplate keyword argument
    hovertemplate_kw = next((kw for kw in pie_call.keywords if kw.arg == "hovertemplate"), None)
    assert hovertemplate_kw is not None, "hovertemplate not found in go.Pie call"

    template_val = ast.literal_eval(hovertemplate_kw.value)
    assert "%{customdata:,.0f}" in template_val, (
        f"hovertemplate must format customdata dollar value, but found: {template_val}"
    )
    assert "%{value:,.0f}" not in template_val, (
        "hovertemplate should not format value with integer dollars as value holds fractional weights"
    )


def test_allocation_chart_render_produces_correct_dollar_amounts():
    """Verify that a go.Pie figure configured with customdata produces correct dollar amounts."""
    labels = ["NVDA", "MSFT", "GOOGL", "ETH-USD"]
    weights = [0.40, 0.30, 0.20, 0.10]
    size = 10000.0
    customdata = [w * size for w in weights]

    pie = go.Pie(
        labels=labels,
        values=weights,
        customdata=customdata,
        hovertemplate="%{label}: %{percent} ($%{customdata:,.0f})<extra></extra>",
    )

    fig = go.Figure(pie)
    trace = fig.data[0]

    assert list(trace.customdata) == [4000.0, 3000.0, 2000.0, 1000.0]
    assert trace.hovertemplate == "%{label}: %{percent} ($%{customdata:,.0f})<extra></extra>"
