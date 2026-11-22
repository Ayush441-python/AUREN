from __future__ import annotations

import logging
import math
import os
import re
from typing import Any, Dict, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from starlette.staticfiles import StaticFiles

from engine.data import load_prices, load_volumes
from engine.env import load_env, setting
from engine.liquidity import avg_daily_value, days_to_exit
from engine.metrics import (
    concentration,
    correlation,
    high_pairs,
    max_drawdown,
    portfolio_returns,
    sector_exposure,
    volatility,
)
from engine.report import ai_report, unverified_numbers
from engine.score import RULE_TABLE, risk_score
from engine.stress import SCENARIOS, stress, worst_periods
from engine.universe import GROUPS, SECTORS, classify_and_register_ticker
from engine.wallet import (
    BASE_RPC,
    holdings_to_portfolio,
    is_valid_address,
    wallet_holdings,
)

# Ensure environment variables are loaded
load_env()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auren-api")

app = FastAPI(
    title="AUREN Risk API",
    version="1.0.0",
    description=(
        "Production API powering AUREN Portfolio & Risk Analytics. "
        "Analytics only, not investment advice."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS setup for frontend / web integrations.
# Browsers reject wildcard origins together with credentials, so we list the
# known origins explicitly and allow any *.vercel.app preview via regex.
# The frontend does not use cookies, so credentials are not needed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://aurenfrontend-five.vercel.app",
        "https://auren-api-8yrq.onrender.com",
        "http://localhost:3000",
        "http://localhost:5500",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5500",
        "http://127.0.0.1:8000",
    ],
    allow_origin_regex=r"^https://.*\.vercel\.app$",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

PERIOD_PATTERN = r"^(\d{1,2}(mo|y)|ytd|max)$"


# --- Request & Response Models ---

class PortfolioRequest(BaseModel):
    weights: Dict[str, float] = Field(
        ...,
        description="Dictionary mapping ticker symbols to weights (percentages or dollar amounts, e.g. {'NVDA': 40, 'AAPL': 30, 'MSFT': 30})",
        json_schema_extra={"example": {"NVDA": 40.0, "AAPL": 30.0, "MSFT": 30.0}},
    )
    period: str = Field(
        default="2y",
        pattern=PERIOD_PATTERN,
        description="Historical price lookback period (e.g. '1y', '2y', '5y')",
    )


class LiquidityRequest(BaseModel):
    portfolio_value: float = Field(
        ...,
        gt=0,
        description="Total monetary value of the portfolio in USD",
        json_schema_extra={"example": 100000.0},
    )
    weights: Dict[str, float] = Field(
        ...,
        description="Ticker to weight mapping",
        json_schema_extra={"example": {"NVDA": 50.0, "AAPL": 50.0}},
    )


class TailHedgeRequest(BaseModel):
    weights: Dict[str, float] = Field(
        ...,
        description="Baseline portfolio weights",
        json_schema_extra={"example": {"NVDA": 50.0, "BTC-USD": 50.0}},
    )
    hedge_asset: str = Field(
        default="GLD",
        description="Defensive asset ticker to introduce for tail-risk hedging",
    )
    hedge_ratio: float = Field(
        default=0.2,
        gt=0.0,
        lt=1.0,
        description="Fraction of the portfolio allocated to the hedge asset",
    )
    period: str = Field(
        default="2y",
        pattern=PERIOD_PATTERN,
        description="Historical lookback period",
    )


# --- Core Risk Computation Logic ---

def _compute_risk_analytics(weights: Dict[str, float], period: str) -> Dict[str, Any]:
    # Normalize weights
    total_w = sum(weights.values())
    if total_w <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sum of portfolio weights must be greater than zero.",
        )
    norm_weights = {k.upper(): v / total_w for k, v in weights.items()}

    tickers = list(norm_weights.keys())
    for t in tickers:
        classify_and_register_ticker(t)

    try:
        prices = load_prices(tickers, period=period)
    except Exception as e:
        logger.error(f"Failed to load prices for tickers {tickers}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to load price data for tickers: {e}",
        )

    if prices.empty:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No price data returned for the given tickers and period.",
        )

    rets = portfolio_returns(prices, norm_weights)
    vol = volatility(rets)
    mdd = max_drawdown(rets)
    conc = concentration(norm_weights)
    corr = correlation(prices)
    hp = high_pairs(corr)
    sect = sector_exposure(norm_weights)
    st = stress(rets)
    wp = worst_periods(rets)

    score, breakdown = risk_score(
        volatility=vol,
        max_drawdown=mdd,
        concentration=conc,
        high_corr_pairs=hp,
        stress_losses=st,
        sectors=sect,
    )

    report = ai_report(
        score=score,
        breakdown=breakdown,
        volatility=vol,
        max_drawdown=mdd,
        stress=st,
        sectors=sect,
    )

    return {
        "risk_score": score,
        "volatility": vol,
        "max_drawdown": mdd,
        "concentration": conc,
        "stress_scenarios": st,
        "worst_periods": wp,
        "sector_exposure": sect,
        "breakdown": breakdown,
        "ai_report": report,
        "normalized_weights": norm_weights,
    }


# --- Endpoints ---

@app.get("/")
def root():
    return RedirectResponse(url="/docs")


@app.post("/risk")
def calculate_risk(payload: PortfolioRequest):
    """
    Compute comprehensive risk metrics, scores, stress tests, and AI report for a portfolio.
    """
    return _compute_risk_analytics(payload.weights, payload.period)


@app.post("/risk/tailhedge")
def tail_hedge_agent(payload: TailHedgeRequest):
    """
    AUREN TailHedge: Automated tail-risk mitigation & hedging agent.
    Evaluates baseline risk, introduces a defensive hedge asset (e.g., GLD, PEP, XEL),
    and verifies risk score and drawdown suppression in a closed loop.
    """
    # 1. Initial Risk Profiling
    baseline = _compute_risk_analytics(payload.weights, payload.period)

    # 2. Hedging Allocation Synthesis
    base_weights = payload.weights
    hedge_asset = payload.hedge_asset.upper()
    hedge_ratio = payload.hedge_ratio

    scaled_weights = {k: v * (1.0 - hedge_ratio) for k, v in base_weights.items()}
    if hedge_asset in scaled_weights:
        scaled_weights[hedge_asset] += hedge_ratio * sum(base_weights.values())
    else:
        scaled_weights[hedge_asset] = hedge_ratio * sum(base_weights.values())

    # 3. Closed-Loop API Verification
    hedged = _compute_risk_analytics(scaled_weights, payload.period)

    # 4. Compute Deltas & Orders
    orders = {}
    for t in set(list(base_weights.keys()) + [hedge_asset]):
        orig_w = base_weights.get(t, 0.0)
        new_w = scaled_weights.get(t, 0.0)
        diff = new_w - orig_w
        if abs(diff) > 1e-4:
            action = "BUY" if diff > 0 else "SELL"
            orders[t] = {"action": action, "delta_weight": round(diff, 4)}

    # 5. Tail-risk mitigation summary
    vol_reduction = baseline["volatility"] - hedged["volatility"]
    mdd_reduction = baseline["max_drawdown"] - hedged["max_drawdown"]

    return {
        "agent": "AUREN TailHedge",
        "status": "success",
        "hedge_asset": hedge_asset,
        "hedge_ratio": hedge_ratio,
        "baseline_metrics": {
            "risk_score": baseline["risk_score"],
            "volatility": baseline["volatility"],
            "max_drawdown": baseline["max_drawdown"],
        },
        "hedged_metrics": {
            "risk_score": hedged["risk_score"],
            "volatility": hedged["volatility"],
            "max_drawdown": hedged["max_drawdown"],
        },
        "risk_suppression": {
            "volatility_reduction": round(vol_reduction, 4),
            "max_drawdown_improvement": round(mdd_reduction, 4),
        },
        "rebalance_orders": orders,
        "hedged_weights": hedged["normalized_weights"],
    }


@app.post("/liquidity")
def calculate_liquidity(payload: LiquidityRequest):
    """
    Compute liquidity, average daily volume, and days-to-exit metrics for a portfolio.
    """
    total_w = sum(payload.weights.values())
    if total_w <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sum of portfolio weights must be greater than zero.",
        )
    norm_weights = {k.upper(): v / total_w for k, v in payload.weights.items()}
    tickers = list(norm_weights.keys())

    for t in tickers:
        classify_and_register_ticker(t)

    try:
        volumes = load_volumes(tickers, period="1y")
    except Exception as e:
        logger.error(f"Failed to load volume data for tickers {tickers}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to load volume data: {e}",
        )

    advs = avg_daily_value(volumes)
    dtes = days_to_exit(payload.portfolio_value, norm_weights, advs)

    return {
        "portfolio_value": payload.portfolio_value,
        "avg_daily_volumes": advs,
        "days_to_exit": dtes,
    }


@app.get("/wallet/{address}")
def analyze_wallet(address: str, period: str = "2y"):
    """
    Analyze risk metrics for an on-chain crypto wallet address.
    """
    if not is_valid_address(address):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid wallet address format.",
        )

    try:
        holdings = wallet_holdings(address)
    except Exception as e:
        logger.error(f"Failed to fetch holdings for {address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch wallet holdings from blockchain RPC: {e}",
        )

    if not holdings:
        return {
            "address": address,
            "holdings": {},
            "message": "No recognized token holdings found for this address.",
        }

    weights = holdings_to_portfolio(holdings)
    if not weights:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not convert wallet holdings to a valid portfolio weighting.",
        )

    result = _compute_risk_analytics(weights, period)
    result["address"] = address
    result["raw_holdings"] = holdings
    return result