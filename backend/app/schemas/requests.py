from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

# 1-99 units, no leading zero: "01y" and "0y" are not periods the provider
# can serve, so admitting them sent every such request to the bundled CSV
# fallback and answered with the whole two-year snapshot instead of the
# requested window (issue #405).
PERIOD_PATTERN = r"^(?:[1-9]\d?(?:mo|y)|ytd|max)$"


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
