# AUREN Python client (API Integration)

A dependency-free Python client for the AUREN portfolio risk engine.
Calls `POST /risk` and returns typed results. **Analytics only, not investment advice.**

- Python 3.10+
- No third-party packages (stdlib `urllib`, `json`, `dataclasses`, `argparse`)

## Install

Nothing to install. Copy `auren_client.py` into your project, or run it directly.

## CLI usage

Start the API first:

```bash
uvicorn api:app --reload --port 8000
```

Then:

```bash
python auren_client.py --weights NVDA=40 MSFT=30 GOOGL=20 ETH-USD=10
```

```
Risk score: 70/100 (High)
  - Largest holding is 40% (over 30%)
  - Behaves like only 3.3 assets
  - 2 pairs of assets move closely together
  - 90.0% sits in one sector
Analytics only, not investment advice.
```

Raw JSON response:

```bash
python auren_client.py --weights NVDA=40 MSFT=30 --json
```

Point at a remote deployment:

```bash
python auren_client.py --base-url https://your-auren-host --weights BTC-USD=60 ETH-USD=40
```

## Library usage

```python
from auren_client import AurenClient, AurenError

client = AurenClient(base_url="http://127.0.0.1:8000", timeout=10, retries=3)

try:
    result = client.risk({"NVDA": 40, "MSFT": 30, "GOOGL": 20, "ETH-USD": 10})
except AurenError as exc:
    raise SystemExit(f"AUREN call failed: {exc}")

print(result.score, result.level)
print(result.reasons)
if result.concentration:
    print(result.concentration.top_asset, result.concentration.effective_assets)
print(result.stress)  # {"Big Tech falls 20%": -0.18, ...}
```

## Response field mapping

| API field | Client attribute | Type |
| :--- | :--- | :--- |
| `score` | `RiskResult.score` | `int` (0-100) |
| `level` | `RiskResult.level` | `str` (`Low` / `Medium` / `High`) |
| `reasons` | `RiskResult.reasons` | `list[str]` |
| `concentration.top_asset` | `Concentration.top_asset` | `str \| None` |
| `concentration.top_weight` | `Concentration.top_weight` | `float` (fraction) |
| `concentration.effective_assets` | `Concentration.effective_assets` | `float` |
| `volatility` | `RiskResult.volatility` | `float \| None` (annualised fraction) |
| `max_drawdown` | `RiskResult.max_drawdown` | `float \| None` (negative fraction) |
| `sector_exposure` | `RiskResult.sector_exposure` | `dict[str, float]` |
| `stress` | `RiskResult.stress` | `dict[str, float]` |
| `disclaimer` | `RiskResult.disclaimer` | `str` |
| *(whole document)* | `RiskResult.raw` | `dict` |

## Behaviour notes

- Weights are percentages and must sum to a positive value; the client validates this before sending.
- Transient network failures are retried `retries` times with exponential backoff (`backoff * 2**attempt`).
- HTTP errors raise `AurenError` containing the status code and the server's response body.
- `client.health()` returns the `GET /` document, useful as a readiness probe.
