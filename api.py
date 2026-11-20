import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from engine.data import load_prices
from engine.metrics import (
    concentration,
    portfolio_returns,
    volatility,
    max_drawdown,
    correlation,
    high_pairs,
    sector_exposure,
)
from engine.score import risk_score
from engine.stress import SCENARIOS, stress
from engine.universe import SECTORS

app = FastAPI(
    title="AUREN Risk API",
    description="Analytics only, not investment advice.",
)


class Portfolio(BaseModel):
    weights: dict[str, float]  # e.g. {"NVDA": 40, "MSFT": 30, "GOOGL": 20, "ETH-USD": 10}


@app.get("/")
def root():
    return {
        "name": "AUREN Risk API",
        "version": "0.1.0",
        "docs": "/docs",
        "disclaimer": "Analytics only, not investment advice.",
    }


@app.post("/risk")
def risk(p: Portfolio):
    if not p.weights:
        raise HTTPException(status_code=400, detail="Portfolio weights cannot be empty")

    unknown = [t for t in p.weights if t not in SECTORS]
    if unknown:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported tickers: {unknown}. Supported tickers: {list(SECTORS.keys())}",
        )

    w = pd.Series(p.weights, dtype=float)
    if (w <= 0).any() or w.sum() <= 0:
        raise HTTPException(
            status_code=400, detail="Weights must be positive numbers summing to > 0"
        )
    w = w / w.sum()

    prices = load_prices(list(w.index))
    if prices.empty:
        raise HTTPException(
            status_code=500, detail="Failed to load historical price series"
        )

    pr = portfolio_returns(prices, w)
    conc = concentration(w)
    vol = volatility(pr)
    mdd = max_drawdown(pr)

    corr = correlation(prices, w.index)
    pairs = high_pairs(corr)
    exposure = sector_exposure(w)

    score, level, hits = risk_score(
        conc, vol, mdd, pairs, float(exposure.max()) if not exposure.empty else 0.0
    )

    return {
        "score": score,
        "level": level,
        "reasons": [why for _, why in hits],
        "concentration": conc,
        "volatility": vol,
        "max_drawdown": mdd,
        "sector_exposure": exposure.to_dict(),
        "correlated_pairs": pairs,
        "stress": {name: stress(w, s) for name, s in SCENARIOS.items()},
        "disclaimer": "Analytics only, not investment advice.",
    }
