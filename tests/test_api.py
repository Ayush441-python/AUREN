from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (200, 307)
    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "online"

def test_healthz():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_universe():
    response = client.get("/universe")
    assert response.status_code == 200
    data = response.json()
    assert "NVDA" in data["sectors"]
    assert "supported_tickers" in data
    assert len(data["supported_tickers"]) > 0

def test_rules():
    response = client.get("/rules")
    assert response.status_code == 200
    assert "rules" in response.json()

def test_risk_valid():
    response = client.post("/risk", json={"weights": {"NVDA": 50, "AAPL": 50}})
    assert response.status_code == 200
    data = response.json()
    assert "score" in data
    assert "level" in data
    assert "concentration" in data
    assert "volatility" in data
    assert "sector_exposure" in data
    assert "stress" in data

def test_risk_invalid_ticker():
    response = client.post("/risk", json={"weights": {"INVALID_TICKER_XYZ": 100}})
    assert response.status_code == 400
    assert "Unsupported tickers" in response.json()["detail"]

def test_risk_empty():
    response = client.post("/risk", json={"weights": {}})
    assert response.status_code == 400

def test_liquidity_valid():
    response = client.post("/liquidity", json={
        "portfolio_value": 100000,
        "weights": {"NVDA": 60, "MSFT": 40},
        "adv_participation": 0.1
    })
    assert response.status_code == 200
    data = response.json()
    assert "assets" in data
    assert len(data["assets"]) == 2
    assert "max_days_to_exit" in data

def test_wallet_invalid_address():
    response = client.post("/wallet", json={"address": "invalid_address"})
    assert response.status_code == 400
    assert "Invalid EVM/Base address" in response.json()["detail"]


def test_risk_mixed_stock_and_crypto_is_json_safe_and_aligned(monkeypatch):
    """Stocks skip weekends, crypto does not. The raw frame has NaN rows; the API must
    drop them so the JSON is valid and every chart series matches `dates`."""
    import numpy as np
    import pandas as pd
    import backend.app.main as api_module

    idx = pd.date_range("2025-01-01", periods=120, freq="D")  # includes weekends
    rng = np.random.default_rng(0)
    frame = pd.DataFrame({
        "NVDA": 100 * (1 + rng.normal(0, 0.01, len(idx))).cumprod(),
        "ETH-USD": 100 * (1 + rng.normal(0, 0.02, len(idx))).cumprod(),
    }, index=idx)
    frame.loc[frame.index.dayofweek >= 5, "NVDA"] = np.nan  # stock closed on weekends

    monkeypatch.setattr(api_module, "load_prices", lambda tickers, period="2y": frame[list(tickers)])

    response = client.post("/risk", json={"weights": {"NVDA": 60, "ETH-USD": 40}})
    assert response.status_code == 200
    data = response.json()
    n = len(data["dates"])
    assert n >= 30
    assert len(data["drawdown_series"]) == n
    for series in data["price_series"].values():
        assert len(series) == n
        assert None not in series


def test_wallet_endpoint_shape(monkeypatch):
    import backend.app.main as api_module

    rows = [{"token": "NVDAc", "ticker": "NVDA", "address": "0x1", "tokens": 2.0, "shares": 2.0,
             "price": 100.0, "value": 200.0, "supported": True, "nav_updated": None}]
    monkeypatch.setattr(api_module, "wallet_holdings",
                        lambda addr, supported, rpc: {"rows": rows, "n_tokens": 5})
    response = client.post("/wallet", json={"address": "0x" + "a" * 40})
    assert response.status_code == 200
    data = response.json()
    assert data["portfolio"] == {"NVDA": 1.0}
    assert data["holdings"][0]["ticker"] == "NVDA"
    assert data["total_value"] == 200.0


def test_risk_drivers_endpoint_sorted_by_score_impact(monkeypatch):
    """Verify /risk returns hits & reasons sorted descending by score impact with stable ties."""
    from pathlib import Path
    import backend.app.services.analytics as analytics_mod

    monkeypatch.setattr(analytics_mod, "risk_score", lambda conc, vol, mdd, pairs, max_sec: (55, "Medium", [
        (20, "Largest holding is 40% (over 30%)"),
        (15, "Behaves like only 3.3 assets"),
        (20, "Volatility is 45% a year (over 30%)"),
    ]))
    data = client.post("/risk", json={"weights": {"NVDA": 40, "AAPL": 60}}).json()
    assert [p for p, _ in data["hits"]] == [20, 20, 15]
    assert data["reasons"] == [
        "Largest holding is 40% (over 30%)",
        "Volatility is 45% a year (over 30%)",
        "Behaves like only 3.3 assets",
    ]

    monkeypatch.setattr(analytics_mod, "risk_score", lambda conc, vol, mdd, pairs, max_sec: (0, "Low", []))
    res_empty = client.post("/risk", json={"weights": {"NVDA": 40, "AAPL": 60}}).json()
    assert res_empty["hits"] == [] and res_empty["reasons"] == []

    monkeypatch.setattr(analytics_mod, "risk_score", lambda conc, vol, mdd, pairs, max_sec: (30, "Low", [(15, "Rule A"), (15, "Rule B")]))
    assert client.post("/risk", json={"weights": {"NVDA": 40, "AAPL": 60}}).json()["reasons"] == ["Rule A", "Rule B"]

    ov = Path("web/src/components/views/OverviewView.tsx").read_text(encoding="utf-8")
    assert "[...data.hits].sort((a, b) => b[0] - a[0])" in ov
    assert "rankedReasons" in ov
