"""AUREN Risk API client.

A dependency-free Python client for the AUREN portfolio risk engine
(https://github.com/Ayush441-python/AUREN). Calls POST /risk and returns
typed results. Analytics only, not investment advice.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Mapping

DEFAULT_BASE_URL = "http://127.0.0.1:8000"
RISK_PATH = "/risk"


class AurenError(RuntimeError):
    """Raised when the AUREN API returns an error or is unreachable."""


@dataclass(frozen=True)
class Concentration:
    top_asset: str | None
    top_weight: float
    effective_assets: float


@dataclass(frozen=True)
class RiskResult:
    score: int
    level: str
    reasons: list[str] = field(default_factory=list)
    concentration: Concentration | None = None
    volatility: float | None = None
    max_drawdown: float | None = None
    sector_exposure: dict[str, float] = field(default_factory=dict)
    stress: dict[str, float] = field(default_factory=dict)
    disclaimer: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RiskResult":
        conc = data.get("concentration")
        concentration = None
        if isinstance(conc, Mapping):
            concentration = Concentration(
                top_asset=conc.get("top_asset"),
                top_weight=float(conc.get("top_weight", 0.0)),
                effective_assets=float(conc.get("effective_assets", 0.0)),
            )
        return cls(
            score=int(data.get("score", 0)),
            level=str(data.get("level", "Unknown")),
            reasons=list(data.get("reasons", [])),
            concentration=concentration,
            volatility=_opt_float(data.get("volatility")),
            max_drawdown=_opt_float(data.get("max_drawdown")),
            sector_exposure=dict(data.get("sector_exposure", {})),
            stress=dict(data.get("stress", {})),
            disclaimer=str(data.get("disclaimer", "")),
            raw=dict(data),
        )


def _opt_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class AurenClient:
    """Minimal client for the AUREN risk API."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 10.0,
        retries: int = 3,
        backoff: float = 0.5,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff

    def _request(self, method: str, path: str, payload: Any = None) -> Any:
        url = f"{self.base_url}{path}"
        data = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        last_err: Exception | None = None
        for attempt in range(self.retries + 1):
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    body = resp.read().decode("utf-8")
                    return json.loads(body) if body else {}
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", "replace")
                raise AurenError(f"HTTP {exc.code} from {url}: {detail}") from exc
            except (urllib.error.URLError, TimeoutError) as exc:
                last_err = exc
                if attempt < self.retries:
                    time.sleep(self.backoff * (2 ** attempt))
                    continue
                raise AurenError(f"Could not reach {url}: {exc}") from exc
        raise AurenError(str(last_err))

    def health(self) -> dict[str, Any]:
        """Return the service health/info document from GET /."""
        return self._request("GET", "/")

    def risk(self, weights: Mapping[str, float]) -> RiskResult:
        """Compute portfolio risk for a mapping of symbol -> percent weight."""
        if not weights:
            raise ValueError("weights must be a non-empty mapping of symbol -> percent")
        total = sum(float(w) for w in weights.values())
        if total <= 0:
            raise ValueError("weights must sum to a positive value")
        payload = {"weights": {str(k): float(v) for k, v in weights.items()}}
        return RiskResult.from_dict(self._request("POST", RISK_PATH, payload))


def _parse_weights(items: list[str]) -> dict[str, float]:
    weights: dict[str, float] = {}
    for item in items:
        if "=" not in item:
            raise argparse.ArgumentTypeError(
                f"invalid weight '{item}', expected SYMBOL=PERCENT"
            )
        symbol, value = item.split("=", 1)
        weights[symbol.strip()] = float(value)
    return weights


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Query the AUREN risk API.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument(
        "--weights",
        nargs="+",
        required=True,
        metavar="SYM=PERCENT",
        help="e.g. --weights NVDA=40 MSFT=30 ETH-USD=30",
    )
    parser.add_argument("--json", action="store_true", help="print raw JSON response")
    args = parser.parse_args(argv)

    client = AurenClient(base_url=args.base_url)
    result = client.risk(_parse_weights(args.weights))

    if args.json:
        print(json.dumps(result.raw, indent=2))
        return 0

    print(f"Risk score: {result.score}/100 ({result.level})")
    for reason in result.reasons:
        print(f"  - {reason}")
    if result.disclaimer:
        print(result.disclaimer)
    return 0


if __name__ == "__main__":
    sys.exit(main())
