"""#376: el VaR paramétrico al 95% tiene que incluir la media, no solo la volatilidad.

El cuantil de pérdida para un horizonte h es -(μ·h − z·σ·√h) con μ y σ diarios.
La versión anterior usaba solo múltiplos de la volatilidad anualizada, así que
una cartera que cae un 1% cada sesión —σ≈0— mostraba 0.0% de VaR en los tres
horizontes. Estos tests fijan los tres casos que importan: caída constante,
oscilación sin tendencia y subida constante.
"""

import pandas as pd
import pytest

from backend.app.services import analytics

BUSINESS_DAYS = 40


def _prices(daily_return: float, days: int = BUSINESS_DAYS) -> pd.DataFrame:
    """Serie geométrica con un rendimiento diario constante."""
    index = pd.bdate_range("2025-01-02", periods=days)
    values = [100 * (1 + daily_return) ** day for day in range(days)]
    return pd.DataFrame({"AAPL": values}, index=index)


def _var_for(prices: pd.DataFrame, monkeypatch) -> dict:
    # Sin red y sin caché: la función recibe las precios ya alineados.
    monkeypatch.setattr(
        analytics, "load_aligned_prices", lambda tickers, period: prices[list(tickers)]
    )
    out = analytics.compute_portfolio_risk({"AAPL": 1}, "1y")
    return out["parametric_var_95"]


def test_steadily_declining_portfolio_reports_the_full_loss(monkeypatch):
    """−1% cada sesión: 1.0%, 10.0% y 21.0%, no 0.0%."""
    var = _var_for(_prices(-0.01), monkeypatch)

    assert var["1d"] == pytest.approx(0.01, abs=1e-6)
    assert var["10d"] == pytest.approx(0.10, abs=1e-6)
    assert var["21d"] == pytest.approx(0.21, abs=1e-6)


def test_oscillation_without_trend_keeps_the_volatility_term(monkeypatch):
    """Media ≈ 0 y volatilidad alta: el VaR lo pone σ, no la media."""
    index = pd.bdate_range("2025-01-02", periods=BUSINESS_DAYS)
    prices = pd.DataFrame({"AAPL": [100, 105, 95, 105, 95] * 8}, index=index)

    var = _var_for(prices, monkeypatch)

    assert var["1d"] > 0.05
    assert var["21d"] > var["1d"]  # la raíz del horizonte sigue escalando


def test_rising_portfolio_can_have_negative_var(monkeypatch):
    """Si gana más rápido de lo que oscila, el cuantil del 95% no es una pérdida."""
    var = _var_for(_prices(0.02), monkeypatch)

    assert var["1d"] < 0


def test_the_block_documents_itself(monkeypatch):
    """Quien lea la respuesta tiene que poder reproducir el número."""
    var = _var_for(_prices(-0.01), monkeypatch)

    assert var["confidence"] == 0.95
    assert var["z"] == pytest.approx(1.6449, abs=1e-4)
    assert var["mean_daily"] == pytest.approx(-0.01, abs=1e-6)
    assert var["stdev_daily"] == pytest.approx(0.0, abs=1e-9)
