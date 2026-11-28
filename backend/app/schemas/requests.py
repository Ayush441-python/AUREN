from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

# Los periodos que el proveedor entiende de verdad. Antes el patrón aceptaba
# ceros delante y ceros sueltos ("01y", "0y", "00y", "0mo", "02mo"): el proveedor
# devolvía vacío para todos ellos y la petición caía en la caché de dos años, con
# HTTP 200 y sin decirlo. Un cero delante no es una ventana: se rechaza en el
# esquema, que es donde se puede explicar. Ver #405.
#
#   ytd | max                      → los dos literales del proveedor
#   1y  2y ... 99y                 → años, sin cero delante
#   1mo 2mo ... 99mo               → meses, sin cero delante
PERIOD_PATTERN = r"^(ytd|max|(?:[1-9]|[1-9]\d)(?:mo|y))$"

# El mismo patrón, para el mensaje de error: lo que sí se acepta.
PERIOD_EXAMPLES = "ytd, max, 1y, 2y, 5y, 1mo, 3mo, 6mo"


class PortfolioRequest(BaseModel):
    weights: Dict[str, float] = Field(
        ...,
        description="Dictionary mapping ticker symbols to weights (percentages or dollar amounts, e.g. {'NVDA': 40, 'AAPL': 30, 'MSFT': 30})",
        json_schema_extra={"example": {"NVDA": 40.0, "AAPL": 30.0, "MSFT": 30.0}},
    )
    period: str = Field(
        default="2y",
        pattern=PERIOD_PATTERN,
        description=f"Historical price lookback period ({PERIOD_EXAMPLES}). A zero-padded or zero period is rejected instead of silently serving the bundled two-year cache.",
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
    period: str = Field(
        default="1y",
        pattern=PERIOD_PATTERN,
        description=f"Lookback window for volume data ({PERIOD_EXAMPLES})",
    )


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
