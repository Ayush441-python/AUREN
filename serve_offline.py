"""Run the AUREN Risk API on the repo's cached price table (deterministic, no network)."""
import engine.data as data
data._download = lambda field, tickers, period: None
from api import app  # noqa: E402,F401
