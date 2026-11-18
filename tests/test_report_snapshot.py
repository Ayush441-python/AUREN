"""Downloaded metrics and narrative must describe the same portfolio."""
from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_report_export_requires_current_metrics():
    root = Path(__file__).resolve().parents[1]
    wrapper = f'''
from pathlib import Path
import runpy
from unittest.mock import patch
import pandas as pd
import streamlit as st

root = Path({str(root)!r})
prices = pd.read_csv(root / "data/prices.csv", index_col=0, parse_dates=True)
volumes = pd.read_csv(root / "data/volume.csv", index_col=0, parse_dates=True)
original_download = st.download_button
st.session_state["test_download"] = None

def capture_download(label, data, *args, **kwargs):
    st.session_state["test_download"] = data
    return original_download(label, data, *args, **kwargs)

def fake_setting(name, default=None):
    return {{"LLM_BASE_URL": "http://localhost:9999/v1", "LLM_MODEL": "offline-test"}}.get(name, default)

def fake_report(metrics, *args, **kwargs):
    ticker, weight = next(iter(metrics["largest_holding"].items()))
    return f"Snapshot: {{ticker}} is the largest holding at {{weight:.1%}}."

with patch("engine.data.load_prices", side_effect=lambda tickers: prices[tickers]), \\
     patch("engine.data.load_volumes", side_effect=lambda tickers: volumes[tickers]), \\
     patch("engine.env.setting", side_effect=fake_setting), \\
     patch("engine.report.ai_report", side_effect=fake_report), \\
     patch("streamlit.download_button", side_effect=capture_download):
    runpy.run_path(str(root / "app.py"), run_name="__main__")
'''
    app = AppTest.from_string(wrapper, default_timeout=45).run()
    assert not app.exception
    assert app.session_state["test_download"] is None

    def generate():
        next(b for b in app.button if b.label == "Generate AI Report").click().run()
        assert not app.exception
        return app.session_state["test_download"]

    initial = generate()
    assert "Largest Holding: NVDA (40.0%)" in initial
    assert "Snapshot: NVDA is the largest holding at 40.0%." in initial

    next(s for s in app.selectbox if s.label == "Portfolio Presets").select(
        "Diversified All-Weather"
    ).run()
    assert not app.exception
    assert any("configuration has changed" in m.value for m in app.markdown)
    assert app.session_state["test_download"] is None

    current = generate()
    assert "Largest Holding: MSFT (20.0%)" in current
    assert "Snapshot: MSFT is the largest holding at 20.0%." in current
    assert "NVDA" not in current
    assert not any("configuration has changed" in m.value for m in app.markdown)

    next(n for n in app.number_input if n.label == "Portfolio size ($)").set_value(
        20000.0
    ).run()
    assert not app.exception
    assert app.session_state["test_download"] is None
