from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from backend.app.main import app
from engine.report import unverified_numbers

client = TestClient(app)
WEB_ROOT = Path(__file__).resolve().parent.parent / "web" / "src"


def _mock_prices(tickers: list[str], rows: int = 120) -> pd.DataFrame:
    dates = pd.date_range("2025-01-01", periods=rows, freq="B")
    rng = np.random.default_rng(42)
    data = {}
    for idx, ticker in enumerate(tickers):
        rets = rng.normal(0.0005, 0.012 + idx * 0.002, size=rows)
        data[ticker] = 100.0 * np.cumprod(1.0 + rets)
    return pd.DataFrame(data, index=dates)


def test_stress_view_zeroed_slider_filtering_avoids_400():
    """api.py rejects zero-weight tickers with HTTP 400; StressView must strip 0 weights before simulating."""
    tsx = (WEB_ROOT / "components" / "views" / "StressView.tsx").read_text(encoding="utf-8")
    assert "value > 0" in tsx
    assert "sandbox?.source === data" in tsx
    assert "onSimulate(normalize(weights))" in tsx

    # Unfiltered 0 weight triggers 400
    bad_res = client.post("/risk", json={"weights": {"NVDA": 50, "MSFT": 0}})
    assert bad_res.status_code == 400

    # Filtered weights succeed cleanly (mock prices to avoid external network flakiness)
    with patch("backend.app.services.analytics.load_prices", return_value=_mock_prices(["NVDA"])):
        good_res = client.post("/risk", json={"weights": {"NVDA": 50}})
    assert good_res.status_code == 200
    assert good_res.json()["normalized_weights"] == {"NVDA": 1.0}


def test_report_view_avoids_hardcoded_eth_btc_correlation_and_technology():
    """ReportView must not hardcode '+0.84 between ETH-USD and BTC-USD' or 'Technology'."""
    tsx = (WEB_ROOT / "components" / "views" / "ReportView.tsx").read_text(encoding="utf-8")
    assert "ETH-USD and BTC-USD" not in tsx
    assert "+0.84" not in tsx
    assert "Object.entries(data.sector_exposure)" in tsx
    assert "data.correlated_pairs.length" in tsx

    # Verify pure-equity portfolio produces zero unverified numbers when checked against engine/report.py
    with patch("backend.app.services.analytics.load_prices", return_value=_mock_prices(["NVDA", "MSFT", "AAPL", "GOOGL"])):
        res_eq = client.post(
            "/risk", json={"weights": {"NVDA": 35, "MSFT": 30, "AAPL": 20, "GOOGL": 15}}
        )
    assert res_eq.status_code == 200
    eq_data = res_eq.json()
    top_sec, top_sec_w = sorted(
        eq_data["sector_exposure"].items(), key=lambda kv: kv[1], reverse=True
    )[0]
    rendered = (
        f"The portfolio scores {eq_data['score']} / 100, placing it in the {eq_data['level']} risk tier. "
        f"The largest single position is {eq_data['concentration']['top_asset']} at "
        f"{eq_data['concentration']['top_weight'] * 100:.1f}%, and the largest sector group is "
        f"{top_sec} at {top_sec_w * 100:.1f}%. Annualized volatility is {eq_data['volatility'] * 100:.1f}% "
        f"and maximum drawdown is {eq_data['max_drawdown'] * 100:.1f}%."
    )
    assert "0.84" not in rendered
    assert unverified_numbers(rendered, eq_data) == []


def test_topbar_and_dashboard_wire_workspace_presets():
    """Both v2 DashboardTopBar/Workstation and legacy TopBar/AppShell/p/[id] must wire workspace switching."""
    dashboard_topbar = (WEB_ROOT / "components" / "dashboard" / "DashboardTopBar.tsx").read_text(
        encoding="utf-8"
    )
    workstation = (WEB_ROOT / "components" / "dashboard" / "Workstation.tsx").read_text(
        encoding="utf-8"
    )
    topbar = (WEB_ROOT / "components" / "shell" / "TopBar.tsx").read_text(encoding="utf-8")
    shell = (WEB_ROOT / "components" / "shell" / "AppShell.tsx").read_text(encoding="utf-8")
    detail_page = (WEB_ROOT / "app" / "p" / "[id]" / "page.tsx").read_text(encoding="utf-8")
    presets = (WEB_ROOT / "lib" / "presets.ts").read_text(encoding="utf-8")

    assert "onApplyPreset(preset.weights, preset.name)" in dashboard_topbar
    assert "onApplyPreset={handleApplyPortfolio}" in workstation
    assert "findPresetWeights" in workstation

    assert "QUICK_WORKSPACES" in presets
    assert "findPresetWeights" in presets
    assert "onSelectPortfolio" in topbar
    assert "onClick={() => setDropdownOpen(false)}" not in topbar
    assert "onSelectPortfolio={onSelectPortfolio}" in shell
    assert "onSelectPortfolio={handleApplyPortfolio}" in detail_page
    assert "onSimulate={handleSimulate}" in detail_page
