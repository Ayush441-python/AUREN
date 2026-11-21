"""Read-only Base wallet support: find Coinbase tokenized stocks in a public address."""
from __future__ import annotations

import pathlib
import re

import pandas as pd
import requests

API_URL = "https://api.coinbase.com/v1/tokenized-stocks"
CACHE = pathlib.Path(__file__).parent.parent / "data" / "prices.csv"
BASE_RPC = "https://mainnet.base.org"
BALANCE_OF = "0x70a08231"  # ERC-20 balanceOf(address)
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")


def is_valid_address(addr: str) -> bool:
    return bool(ADDRESS_RE.match(addr.strip()))


def underlying_ticker(symbol: str) -> str:
    """NVDAc -> NVDA. Only a label: tokens are identified by contract address."""
    return symbol[:-1] if len(symbol) > 1 and symbol.endswith("c") else symbol


def list_tokenized_stocks(timeout: int = 20) -> list[dict]:
    tokens, page_token = [], None
    for _ in range(20):  # safety cap on pages
        params = {"page_size": 500}
        if page_token:
            params["page_token"] = page_token
        r = requests.get(API_URL, params=params, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        tokens += data.get("tokens", [])
        page_token = data.get("next_page_token")
        if not page_token:
            break
    return tokens


def token_balances(wallet: str, tokens: list[dict], rpc_url: str = BASE_RPC,
                   chunk: int = 50, timeout: int = 30) -> dict:
    """Return {contract_address_lowercase: balance in token units} for non-zero balances."""
    call_data = BALANCE_OF + wallet.strip().lower().removeprefix("0x").rjust(64, "0")
    out = {}
    for i in range(0, len(tokens), chunk):
        part = tokens[i:i + chunk]
        payload = [
            {"jsonrpc": "2.0", "id": j, "method": "eth_call",
             "params": [{"to": t["contract_address"], "data": call_data}, "latest"]}
            for j, t in enumerate(part)
        ]
        r = requests.post(rpc_url, json=payload, timeout=timeout)
        r.raise_for_status()
        resp = r.json()
        if isinstance(resp, dict):  # the RPC rejected the batch
            raise RuntimeError(resp.get("error", {}).get("message", "RPC rejected the request"))
        for item in resp:
            result = item.get("result")
            if not result or result == "0x":
                continue
            raw = int(result, 16)
            if raw > 0:
                t = part[item["id"]]
                out[t["contract_address"].lower()] = raw / 10 ** int(t.get("decimals", 18))
    return out


def _latest_underlying_prices(tickers: list[str]) -> dict[str, float]:
    """Return latest valid close price per ticker from cached or live price data."""
    if not tickers:
        return {}
    out: dict[str, float] = {}
    try:
        if CACHE.exists():
            cached = pd.read_csv(CACHE, index_col=0, parse_dates=True)
            for t in tickers:
                if t in cached.columns:
                    s = cached[t].dropna()
                    if not s.empty and float(s.iloc[-1]) > 0:
                        out[t] = float(s.iloc[-1])
        missing = [t for t in tickers if t not in out]
        if missing:
            from engine.data import load_prices
            df = load_prices(missing)
            for t in missing:
                if t in df.columns:
                    s = df[t].dropna()
                    if not s.empty and float(s.iloc[-1]) > 0:
                        out[t] = float(s.iloc[-1])
    except Exception:
        pass
    return out


def wallet_holdings(wallet: str, supported: set, rpc_url: str = BASE_RPC,
                    fallback_prices: dict[str, float] | None = None) -> dict:
    tokens = list_tokenized_stocks()
    balances = token_balances(wallet, tokens, rpc_url)
    by_addr = {t["contract_address"].lower(): t for t in tokens}
    missing_nav_tickers = []
    for addr in balances:
        t = by_addr[addr]
        ticker = underlying_ticker(t.get("symbol", "?"))
        if float(t.get("nav_price") or 0) <= 0 and ticker in supported:
            missing_nav_tickers.append(ticker)
    ref_prices = dict(fallback_prices) if fallback_prices is not None else _latest_underlying_prices(sorted(set(missing_nav_tickers)))
    rows = []
    for addr, amount in balances.items():
        t = by_addr[addr]
        symbol = t.get("symbol", "?")
        ticker = underlying_ticker(symbol)
        multiplier = float(t.get("multiplier") or 1.0)
        shares = amount * multiplier
        nav_price = float(t.get("nav_price") or 0)
        if nav_price > 0:
            price = nav_price
        elif ticker in ref_prices and ref_prices[ticker] > 0:
            price = float(ref_prices[ticker]) * multiplier
        else:
            price = 0.0
        rows.append({
            "token": symbol, "ticker": ticker, "address": addr,
            "tokens": amount, "shares": shares,
            "price": price, "value": amount * price,
            "supported": ticker in supported,
            "nav_updated": t.get("nav_price_updated_at"),
        })
    rows.sort(key=lambda r: r["value"], reverse=True)
    return {"rows": rows, "n_tokens": len(tokens)}


def holdings_to_portfolio(rows: list[dict],
                          fallback_prices: dict[str, float] | None = None):
    """Aggregate supported holdings by underlying ticker.
    Returns (portfolio_df with ticker + weight %, total_value, skipped_rows)."""
    missing_tickers = [
        r["ticker"] for r in rows
        if r.get("supported") and float(r.get("value") or 0) <= 0
        and (float(r.get("shares") or 0) > 0 or float(r.get("tokens") or 0) > 0)
    ]
    ref_prices = (
        dict(fallback_prices)
        if fallback_prices is not None
        else (_latest_underlying_prices(sorted(set(missing_tickers))) if missing_tickers else {})
    )
    value_by_ticker, skipped = {}, []
    for r in rows:
        val = float(r.get("value") or 0)
        if r.get("supported") and val <= 0 and r["ticker"] in ref_prices:
            underlying = float(ref_prices[r["ticker"]])
            shares = float(r.get("shares") or r.get("tokens") or 0)
            if underlying > 0 and shares > 0:
                val = shares * underlying
                tokens_amt = float(r.get("tokens") or shares)
                r["price"] = val / tokens_amt if tokens_amt > 0 else underlying
                r["value"] = val
        if r.get("supported") and val > 0:
            value_by_ticker[r["ticker"]] = value_by_ticker.get(r["ticker"], 0.0) + val
        else:
            skipped.append(r)
    total = sum(value_by_ticker.values())
    if total <= 0:
        return pd.DataFrame(columns=["ticker", "weight"]), 0.0, skipped
    df = pd.DataFrame({"ticker": list(value_by_ticker),
                       "weight": [v / total * 100 for v in value_by_ticker.values()]})
    return df, total, skipped