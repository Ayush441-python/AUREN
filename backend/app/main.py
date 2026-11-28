import logging
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.staticfiles import StaticFiles

from engine.env import load_env
import engine.data as _data
import engine.wallet as _wallet
from backend.app.core.config import settings
from backend.app.api.router import api_router
from backend.app.services.analytics import (
    normalize_and_validate_weights as _normalize_and_validate_weights,
    load_aligned_prices as _load_aligned_prices,
    compute_portfolio_risk,
    compute_portfolio_liquidity,
    inspect_wallet_address,
    generate_report_narrative,
)

# Aliases used in tests and monkeypatching
load_prices = _data.load_prices
load_volumes = _data.load_volumes
wallet_holdings = _wallet.wallet_holdings

# Load environment variables
load_env()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auren-api")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Production API powering AUREN Portfolio & Risk Analytics. "
        "Analytics only, not investment advice."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Optional static frontend mounting if present
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/app", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


@app.get("/", tags=["Health & Info"])
def root(request: Request):
    accept = request.headers.get("accept", "")
    if "text/html" in accept and "application/json" not in accept:
        return RedirectResponse(url="/dashboard", status_code=307)
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs": "/docs",
        "redoc": "/redoc",
        "disclaimer": "Analytics only, not investment advice. Past data does not predict the future.",
    }


__all__ = [
    "app",
    "_normalize_and_validate_weights",
    "_load_aligned_prices",
    "compute_portfolio_risk",
    "compute_portfolio_liquidity",
    "inspect_wallet_address",
    "generate_report_narrative",
    "load_prices",
    "load_volumes",
    "wallet_holdings",
]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
