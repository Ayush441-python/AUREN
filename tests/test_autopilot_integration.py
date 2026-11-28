import pytest
from examples.auren_risk_autopilot import synthesize_deescalated_weights


def test_synthesize_deescalated_weights_diversifies_concentrated_book():
    proposed = synthesize_deescalated_weights(
        {"NVDA": 0.40, "MSFT": 0.30, "GOOGL": 0.20, "ETH-USD": 0.10}
    )
    assert sum(proposed.values()) == pytest.approx(1.0, abs=1e-3)
    assert max(proposed.values()) <= 0.25
    assert len(proposed) >= 8
    for ballast in ("GLD", "TLT", "SPY", "JPM"):
        assert ballast in proposed
