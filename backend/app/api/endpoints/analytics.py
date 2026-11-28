import pathlib
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from engine.universe import GROUPS, SECTORS
from engine.score import RULE_TABLE
from engine.wallet import encode_risk_attestation_calldata, decode_erc8021_calldata
from engine.o1_exchange import fetch_o1_alpha_tokens
from backend.app.core.config import settings
from backend.app.schemas import (
    PortfolioRequest,
    LiquidityRequest,
    AIReportRequest,
    WalletRequest,
    AttestEncodeRequest,
    AttestDecodeRequest,
    RebalanceRequest,
)
from backend.app.services.analytics import (
    compute_portfolio_risk,
    compute_portfolio_liquidity,
    inspect_wallet_address,
    generate_report_narrative,
    compute_o1_rebalance,
)

router = APIRouter()
FRONTEND_HTML_PATH = pathlib.Path(__file__).resolve().parents[4] / "frontend" / "index.html"


@router.get("/healthz", tags=["Health & Info"])
def health_check():
    """Render/Kubernetes healthcheck endpoint."""
    return {"status": "healthy"}


@router.get("/universe", tags=["Universe"])
def get_universe():
    """Return list of supported tickers, sectors, and curated market groups."""
    return {
        "sectors": SECTORS,
        "groups": GROUPS,
        "supported_tickers": sorted(list(SECTORS.keys())),
    }


@router.post("/risk", tags=["Risk Analytics"])
def compute_risk(payload: PortfolioRequest):
    """Compute comprehensive risk score, volatility, drawdowns, correlation, sector exposures, and scenario stress tests."""
    return compute_portfolio_risk(payload.weights, payload.period)


@router.post("/liquidity", tags=["Liquidity Analytics"])
def compute_liquidity(payload: LiquidityRequest):
    """Calculate liquidity analysis: average daily trading value and estimated days to exit positions."""
    return compute_portfolio_liquidity(
        portfolio_value=payload.portfolio_value,
        weights=payload.weights,
        adv_participation=payload.adv_participation,
        period=payload.period,
    )


@router.post("/wallet", tags=["Wallet"])
def inspect_wallet(payload: WalletRequest):
    """Inspect a public Base EVM address for tokenized stock assets and map them to portfolio weights."""
    rpc = payload.rpc_url or settings.BASE_RPC_URL
    return inspect_wallet_address(payload.address, rpc)


@router.post("/report", tags=["AI Risk Analyst"])
def generate_ai_report(payload: AIReportRequest):
    """Generate an AI risk narrative using LLM (Groq or compatible OpenAI endpoint)."""
    base_url = settings.LLM_BASE_URL
    model = payload.model or settings.LLM_MODEL
    api_key = settings.LLM_API_KEY
    return generate_report_narrative(payload.metrics, model, base_url, api_key)


@router.get("/rules", tags=["Risk Analytics"])
def get_rules():
    """Return risk penalty scoring table and thresholds."""
    return {"rules": RULE_TABLE}


@router.post("/attest/encode", tags=["Base Mainnet Attestation"])
def encode_onchain_attestation(payload: AttestEncodeRequest):
    """Encode a deterministic portfolio risk audit into Base Mainnet calldata with ERC-8021 Builder Code suffix."""
    return encode_risk_attestation_calldata(
        score=payload.score,
        level=payload.level,
        top_asset=payload.top_asset,
        portfolio_name=payload.portfolio_name,
        builder_code=payload.builder_code,
    )


@router.post("/attest/decode", tags=["Base Mainnet Attestation"])
def decode_onchain_attestation(payload: AttestDecodeRequest):
    """Decode Base Mainnet transaction calldata to verify AUREN audit proof and ERC-8021 Builder Code."""
    return decode_erc8021_calldata(payload.calldata)


@router.get("/o1/alpha-tokens", tags=["o1 Exchange Integration"])
def get_o1_alpha_tokens(networkId: int = Query(default=8453, description="EVM Network ID (8453 for Base Mainnet)")):
    """Fetch ranked o1 Alpha token contract addresses on Base Mainnet (networkId=8453) enriched with B20 metadata."""
    if networkId <= 0:
        raise HTTPException(status_code=400, detail="networkId must be a positive integer")
    return fetch_o1_alpha_tokens(network_id=networkId)


@router.post("/rebalance", tags=["o1 Exchange Integration"])
def compute_rebalance_orders(payload: RebalanceRequest):
    """Deterministically compute Risk-to-Rebalance trade legs and o1 Exchange Trading API (/api/v2/order) payloads."""
    return compute_o1_rebalance(
        weights=payload.weights,
        portfolio_value=payload.portfolio_value,
        period=payload.period,
        builder_code=payload.builder_code,
    )


@router.get("/attest", response_class=HTMLResponse, tags=["Base Mainnet Attestation"])
@router.get("/dashboard", response_class=HTMLResponse, tags=["Base Mainnet Attestation"])
def live_base_mainnet_workstation():
    """Serve the full Institutional AUREN Workstation & Base Mainnet ERC-8021 Attestation UI."""
    if FRONTEND_HTML_PATH.is_file():
        return FRONTEND_HTML_PATH.read_text(encoding="utf-8")
    return "<h1>AUREN Workstation Not Found</h1>"
