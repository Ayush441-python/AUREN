import re
import sys
from typing import Dict, List
import pandas as pd
from fastapi import HTTPException, status

import engine.wallet as wallet_mod
from engine.data import load_prices, load_volumes
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
)
from backend.app.utils.serializers import finite, json_safe


def normalize_and_validate_weights(weights: Dict[str, float]) -> pd.Series:
    if not weights:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Portfolio weights cannot be empty",
        )

    clean_weights: Dict[str, float] = {}
    for k, v in weights.items():
        key = k.strip().upper()
        if key in {"ETH", "BTC", "SOL", "DOGE", "AVAX", "LINK", "SUI"}:
            key = f"{key}-USD"
        clean_weights[key] = clean_weights.get(key, 0.0) + v

    unknown = []
    for t in clean_weights:
        if t not in SECTORS:
            if re.match(r"^[A-Z0-9\.\-]{1,10}$", t) and not t.startswith("INVALID"):
                try:
                    classify_and_register_ticker(t)
                except Exception:
                    unknown.append(t)
            else:
                unknown.append(t)

    if unknown:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported tickers: {unknown}. Supported tickers: {sorted(list(SECTORS.keys()))}",
        )

    w = pd.Series(clean_weights, dtype=float)
    if (w <= 0).any() or w.sum() <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Weights must be positive numbers summing to > 0",
        )

    return w / w.sum()


def _get_load_prices_fn():
    main_mod = sys.modules.get("backend.app.main")
    if main_mod and hasattr(main_mod, "load_prices"):
        return main_mod.load_prices
    return load_prices


def _get_load_volumes_fn():
    main_mod = sys.modules.get("backend.app.main")
    if main_mod and hasattr(main_mod, "load_volumes"):
        return main_mod.load_volumes
    return load_volumes


def _get_wallet_holdings_fn():
    main_mod = sys.modules.get("backend.app.main")
    if main_mod and hasattr(main_mod, "wallet_holdings"):
        return main_mod.wallet_holdings
    return wallet_mod.wallet_holdings


def load_aligned_prices(tickers: List[str], period: str) -> pd.DataFrame:
    fetcher = _get_load_prices_fn()
    prices = fetcher(tickers, period=period)
    if prices.empty and period != "1y":
        prices = fetcher(tickers, period="1y")

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

    aligned = prices[tickers].ffill(limit=3).dropna()
    if len(aligned) < 30:
        aligned = prices[tickers].dropna()

    if len(aligned) < 30:
        short_tickers = [t for t in tickers if len(prices[t].dropna()) < 30]
        culprit = f" Short history: {short_tickers}." if short_tickers else ""
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Not enough overlapping price history for these tickers (need at least 30 trading days).{culprit}",
        )
    return aligned


def compute_portfolio_risk(weights: Dict[str, float], period: str = "2y") -> dict:
    w = normalize_and_validate_weights(weights)
    tickers = list(w.index)

    prices = load_aligned_prices(tickers, period)

    pr = portfolio_returns(prices, w)
    conc = concentration(w)
    vol = finite(volatility(pr))
    mdd = finite(max_drawdown(pr))

    corr = correlation(prices, w.index).fillna(0.0)
    pairs = high_pairs(corr)
    exposure = sector_exposure(w)

    max_sec_exp = float(exposure.max()) if not exposure.empty else 0.0
    score, level, hits = risk_score(conc, vol, mdd, pairs, max_sec_exp)

    historical_worst = worst_periods(pr)

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
            "top_weight": round(conc["top_weight"], 6),
            "top3_weight": round(conc["top3_weight"], 4),
            "hhi": round(conc["hhi"], 4),
            "effective_assets": round(conc["effective_assets"], 2),
            "exceeds_30pct": conc.get("exceeds_30pct", bool(conc["top_weight"] > 0.30)),
        },
        "volatility": round(vol, 4),
        "max_drawdown": round(mdd, 4),
        "sector_exposure": {k: round(v, 4) for k, v in exposure.to_dict().items()},
        "correlated_pairs": pairs,
        "stress": {name: round(stress(w, s), 4) for name, s in SCENARIOS.items()},
        "worst_historical_periods": {
            k: round(finite(v), 4) if isinstance(v, (int, float)) else v
            for k, v in historical_worst.items()
        },
        "disclaimer": "Analytics only, not investment advice.",
    }
    return json_safe(result)


def compute_portfolio_liquidity(
    portfolio_value: float,
    weights: Dict[str, float],
    adv_participation: float = 0.10,
    period: str = "1y",
) -> dict:
    w = normalize_and_validate_weights(weights)
    tickers = list(w.index)

    fetch_prices = _get_load_prices_fn()
    fetch_volumes = _get_load_volumes_fn()
    prices = fetch_prices(tickers, period=period)
    volumes = fetch_volumes(tickers, period=period)

    if prices.empty or volumes.empty:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to load price or volume data for liquidity calculations",
        )

    adv = avg_daily_value(prices, volumes)
    dollar_holdings = pd.Series({t: float(portfolio_value * w[t]) for t in tickers}, dtype=float)
    exit_days = days_to_exit(dollar_holdings, adv, participation=adv_participation)

    results = []
    for t in tickers:
        adv_t = float(adv.get(t, float("nan")))
        days_t = float(exit_days.get(t, float("nan")))
        results.append({
            "ticker": t,
            "weight": round(float(w[t]), 4),
            "holding_value": round(dollar_holdings[t], 2),
            "adv": round(adv_t, 2) if finite(adv_t) else None,
            "days_to_exit": round(days_t, 2) if finite(days_t) else None,
        })

    max_days = max((r["days_to_exit"] for r in results if r["days_to_exit"] is not None), default=0.0)

    return json_safe({
        "portfolio_value": portfolio_value,
        "adv_participation": adv_participation,
        "max_days_to_exit": max_days,
        "assets": results,
    })


def inspect_wallet_address(address: str, rpc_url: str | None = None) -> dict:
    if not is_valid_address(address):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid EVM/Base address: '{address}'. Expected format 0x followed by 40 hex characters.",
        )

    rpc = rpc_url or BASE_RPC
    fetch_wallet = _get_wallet_holdings_fn()

    try:
        info = fetch_wallet(address, set(SECTORS), rpc)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error querying on-chain wallet data: {str(e)}",
        )

    rows = info["rows"]
    df, total, skipped = holdings_to_portfolio(rows)
    portfolio = {str(r["ticker"]): round(float(r["weight"]) / 100, 6) for _, r in df.iterrows()}
    has_holdings = len(portfolio) > 0 and total > 0

    return json_safe({
        "address": address,
        "holdings_count": len(rows),
        "tokens_checked": info.get("n_tokens", 0),
        "holdings": rows,
        "portfolio": portfolio,
        "total_value": round(float(total), 2),
        "skipped_count": len(skipped),
        "has_holdings": has_holdings,
        "message": (
            f"Successfully loaded {len(portfolio)} portfolio asset{'s' if len(portfolio) > 1 else ''}."
            if has_holdings
            else "No supported tokenized stocks or crypto found in this wallet. You can enter holdings manually or choose a preset."
        ),
    })


def generate_report_narrative(metrics: dict, model: str, base_url: str, api_key: str) -> dict:
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM API key is not configured. Please set LLM_API_KEY environment variable.",
        )

    try:
        report_text = ai_report(metrics, base_url=base_url, api_key=api_key, model=model)
        unverified = unverified_numbers(report_text, metrics)
        return {
            "report": report_text,
            "model": model,
            "unverified_numbers": unverified,
            "disclaimer": "Analytics only, not investment advice. Past data does not predict the future.",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate AI report: {str(e)}",
        )
