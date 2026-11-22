from __future__ import annotations

import logging
import math
import os
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
from engine.universe import GROUPS, SECTORS
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
    adv_participation: float = Field(
        default=0.10,
        gt=0,
        le=1.0,
        description="Max acceptable daily volume participation rate (default 10%)",
    )
    period: str = Field(default="1y", pattern=PERIOD_PATTERN, description="Lookback window for volume data")


class AIReportRequest(BaseModel):
    metrics: Dict[str, Any] = Field(
        ...,
        description="Risk metrics dictionary (output from /risk)",
    )
    model: Optional[str] = Field(
        default=None,
        description="Override LLM model name (defaults to server config or GROQ_MODEL)",
    )


class WalletRequest(BaseModel):
    address: str = Field(
        ...,
        description="Base / EVM wallet address (0x...)",
        json_schema_extra={"example": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"},
    )
    rpc_url: Optional[str] = Field(
        default=None,
        description="Optional Base RPC node URL. Defaults to public Base RPC or BASE_RPC_URL environment variable.",
    )


# --- Helper Methods ---

def _finite(x: Any, default: float = 0.0) -> float:
    """float(x), or `default` if it is NaN / inf / not a number.
    NaN is not valid JSON, so one stray NaN would turn a whole response into a 500."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return default
    return v if math.isfinite(v) else default


def _json_safe(obj: Any) -> Any:
    """Recursively make a response JSON-safe: numpy scalars -> Python, NaN/inf -> None."""
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    if hasattr(obj, "item") and not isinstance(obj, (str, bytes)):
        try:
            obj = obj.item()
        except Exception:
            pass
    if isinstance(obj, float) and not math.isfinite(obj):
        return None
    return obj


def _normalize_and_validate_weights(weights: Dict[str, float]) -> pd.Series:
    if not weights:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Portfolio weights cannot be empty",
        )

    # Normalize ticker symbols to uppercase (merge duplicates after cleaning)
    clean_weights: Dict[str, float] = {}
    for k, v in weights.items():
        key = k.strip().upper()
        clean_weights[key] = clean_weights.get(key, 0.0) + v

    unknown = [t for t in clean_weights if t not in SECTORS]
    if unknown:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported tickers: {unknown}. Supported tickers: {list(SECTORS.keys())}",
        )

    w = pd.Series(clean_weights, dtype=float)
    if (w <= 0).any() or w.sum() <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Weights must be positive numbers summing to > 0",
        )

    return w / w.sum()


def _load_aligned_prices(tickers: list[str], period: str) -> pd.DataFrame:
    """Prices for exactly `tickers`, restricted to days where every ticker traded.

    Stocks skip weekends but crypto does not, so the raw frame has NaN rows.
    The Streamlit app dropna()s for the same reason; the API must too, otherwise
    NaN leaks into the JSON and the response fails.
    """
    prices = load_prices(tickers, period=period)
    if prices.empty:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to load historical price series. Yahoo Finance may be rate-limiting; try again shortly.",
        )
    missing = [t for t in tickers if t not in prices.columns]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"No price data available for: {missing}. Try again shortly or remove them.",
        )
    prices = prices[tickers].dropna()
    if len(prices) < 30:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Not enough overlapping price history for these tickers (need at least 30 trading days).",
        )
    return prices


# Serve the web frontend from the API itself (http://127.0.0.1:8000/app/)
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/app", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


@app.get("/", tags=["Health & Info"])
def root():
    if os.path.isdir(FRONTEND_DIR):
        return RedirectResponse(url="/app/")
    return {
        "name": "AUREN Risk API",
        "version": "1.0.0",
        "status": "online",
        "frontend": "/app/",
        "docs": "/docs",
        "redoc": "/redoc",
        "disclaimer": "Analytics only, not investment advice. Past data does not predict the future.",
    }


@app.get("/healthz", tags=["Health & Info"])
def health_check():
    """Render/Kubernetes healthcheck endpoint."""
    return {"status": "healthy"}


@app.get("/universe", tags=["Universe"])
def get_universe():
    """Return list of supported tickers, sectors, and curated market groups."""
    return {
        "sectors": SECTORS,
        "groups": GROUPS,
        "supported_tickers": sorted(list(SECTORS.keys())),
    }


@app.post("/risk", tags=["Risk Analytics"])
def compute_risk(payload: PortfolioRequest):
    """Compute comprehensive risk score, volatility, drawdowns, correlation, sector exposures, and scenario stress tests."""
    w = _normalize_and_validate_weights(payload.weights)
    tickers = list(w.index)

    prices = _load_aligned_prices(tickers, payload.period)

    pr = portfolio_returns(prices, w)
    conc = concentration(w)
    vol = _finite(volatility(pr))
    mdd = _finite(max_drawdown(pr))

    rets = prices[list(w.index)].dropna().pct_change().dropna()
    corr = rets.corr().fillna(0.0)
    pairs = high_pairs(corr, returns=rets)
    exposure = sector_exposure(w)

    max_sec_exp = float(exposure.max()) if not exposure.empty else 0.0
    score, level, hits = risk_score(conc, vol, mdd, pairs, max_sec_exp)

    # Worst historical drawdown periods
    historical_worst = worst_periods(pr)

    # Series for the interactive charts. Every series has exactly one point per
    # date in `dates` (the portfolio series start at the base value on day 0),
    # so the frontend can plot them against the same x-axis.
    start = prices.index[0]
    norm_prices = (prices / prices.iloc[0] * 100).round(2)

    value = (1 + pr).cumprod()
    cum_ret = pd.concat([pd.Series([1.0], index=[start]), value]) * 100
    dd = value / value.cummax() - 1
    dd_series = pd.concat([pd.Series([0.0], index=[start]), dd])

    dates = [d.strftime("%Y-%m-%d") for d in prices.index]

    price_series = {col: norm_prices[col].tolist() for col in norm_prices.columns}
    price_series["Portfolio"] = cum_ret.round(2).tolist()

    corr_matrix = {
        "columns": list(corr.columns),
        "data": [[round(float(v), 2) for v in row] for row in corr.values],
    }

    result = {
        "score": score,
        "level": level,
        "normalized_weights": {k: round(v, 4) for k, v in w.to_dict().items()},
        "reasons": [why for _, why in hits],
        "hits": hits,
        "dates": dates,
        "price_series": price_series,
        "drawdown_series": dd_series.round(4).tolist(),
        "correlation_matrix": corr_matrix,
        "concentration": {
            "top_asset": conc["top_asset"],
            "top_weight": round(conc["top_weight"], 4),
            "top3_weight": round(conc["top3_weight"], 4),
            "hhi": round(conc["hhi"], 4),
            "effective_assets": round(conc["effective_assets"], 2),
        },
        "volatility": round(vol, 4),
        "max_drawdown": round(mdd, 4),
        "sector_exposure": {k: round(v, 4) for k, v in exposure.to_dict().items()},
        "correlated_pairs": pairs,
        "stress": {name: round(stress(w, s), 4) for name, s in SCENARIOS.items()},
        "worst_historical_periods": {
            k: round(_finite(v), 4) if isinstance(v, (int, float)) else v
            for k, v in historical_worst.items()
        },
        "disclaimer": "Analytics only, not investment advice.",
    }
    return _json_safe(result)


@app.post("/liquidity", tags=["Liquidity Analytics"])
def compute_liquidity(payload: LiquidityRequest):
    """Calculate liquidity analysis: average daily trading value and estimated days to exit positions."""
    w = _normalize_and_validate_weights(payload.weights)
    tickers = list(w.index)

    prices = load_prices(tickers, period=payload.period)
    volumes = load_volumes(tickers, period=payload.period)

    if prices.empty or volumes.empty:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to load price or volume data for liquidity calculations",
        )

    adv = avg_daily_value(prices, volumes)
    dollar_holdings = pd.Series({t: float(payload.portfolio_value * w[t]) for t in tickers}, dtype=float)
    exit_days = days_to_exit(dollar_holdings, adv, participation=payload.adv_participation)

    results = []
    for t in tickers:
        adv_t = float(adv.get(t, float("nan")))
        days_t = float(exit_days.get(t, float("nan")))
        results.append({
            "ticker": t,
            "weight": round(float(w[t]), 4),
            "holding_value": round(dollar_holdings[t], 2),
            "adv": round(adv_t, 2) if math.isfinite(adv_t) else None,
            "days_to_exit": round(days_t, 2) if math.isfinite(days_t) else None,
        })

    max_days = max((r["days_to_exit"] for r in results if r["days_to_exit"] is not None), default=0.0)

    return _json_safe({
        "portfolio_value": payload.portfolio_value,
        "adv_participation": payload.adv_participation,
        "max_days_to_exit": max_days,
        "assets": results,
    })


@app.post("/wallet", tags=["Wallet"])
def inspect_wallet(payload: WalletRequest):
    """Inspect a public Base EVM address for tokenized stock assets and map them to portfolio weights."""
    if not is_valid_address(payload.address):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid EVM/Base address: '{payload.address}'. Expected format 0x followed by 40 hex characters.",
        )

    rpc = payload.rpc_url or setting("BASE_RPC_URL") or BASE_RPC

    try:
        info = wallet_holdings(payload.address, set(SECTORS), rpc)
    except Exception as e:
        logger.error(f"Error querying wallet: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error querying on-chain wallet data: {str(e)}",
        )

    rows = info["rows"]
    df, total, skipped = holdings_to_portfolio(rows)
    # {ticker: weight as a fraction of 1}, which is what the frontend expects
    portfolio = {str(r["ticker"]): round(float(r["weight"]) / 100, 6) for _, r in df.iterrows()}

    return _json_safe({
        "address": payload.address,
        "holdings_count": len(rows),
        "tokens_checked": info.get("n_tokens", 0),
        "holdings": rows,
        "portfolio": portfolio,
        "total_value": round(float(total), 2),
        "skipped_count": len(skipped),
    })


@app.post("/report", tags=["AI Risk Analyst"])
def generate_ai_report(payload: AIReportRequest):
    """Generate an AI risk narrative using LLM (Groq or compatible OpenAI endpoint)."""
    base_url = setting("LLM_BASE_URL") or os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    model = payload.model or setting("LLM_MODEL") or os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
    api_key = setting("LLM_API_KEY") or os.getenv("LLM_API_KEY", "")

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM API key is not configured. Please set LLM_API_KEY environment variable.",
        )

    try:
        report_text = ai_report(payload.metrics, base_url=base_url, api_key=api_key, model=model)
        unverified = unverified_numbers(report_text, payload.metrics)
        return {
            "report": report_text,
            "model": model,
            "unverified_numbers": unverified,
            "disclaimer": "Analytics only, not investment advice. Past data does not predict the future.",
        }
    except Exception as e:
        logger.error(f"Error generating AI report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate AI report: {str(e)}",
        )


@app.get("/rules", tags=["Risk Analytics"])
def get_rules():
    """Return risk penalty scoring table and thresholds."""
    return {"rules": RULE_TABLE}
