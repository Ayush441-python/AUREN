"""Read-only Base wallet support: find Coinbase tokenized stocks in a public address."""
import re

import pandas as pd
import requests

API_URL = "https://api.coinbase.com/v1/tokenized-stocks"
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


def wallet_holdings(wallet: str, supported: set, rpc_url: str = BASE_RPC) -> dict:
    tokens = list_tokenized_stocks()
    balances = token_balances(wallet, tokens, rpc_url)
    by_addr = {t["contract_address"].lower(): t for t in tokens}
    rows = []
    for addr, amount in balances.items():
        t = by_addr[addr]
        symbol = t.get("symbol", "?")
        ticker = underlying_ticker(symbol)
        price = float(t.get("nav_price") or 0)      # reference value per token
        multiplier = float(t.get("multiplier") or 1.0)
        rows.append({
            "token": symbol, "ticker": ticker, "address": addr,
            "tokens": amount, "shares": amount * multiplier,
            "price": price, "value": amount * price,
            "supported": ticker in supported,
            "nav_updated": t.get("nav_price_updated_at"),
        })
    rows.sort(key=lambda r: r["value"], reverse=True)
    return {"rows": rows, "n_tokens": len(tokens)}


def holdings_to_portfolio(rows: list[dict]):
    """Aggregate supported holdings by underlying ticker.
    Returns (portfolio_df with ticker + weight %, total_value, skipped_rows)."""
    value_by_ticker, skipped = {}, []
    for r in rows:
        if r["supported"] and r["value"] > 0:
            value_by_ticker[r["ticker"]] = value_by_ticker.get(r["ticker"], 0.0) + r["value"]
        else:
            skipped.append(r)
    total = sum(value_by_ticker.values())
    if total <= 0:
        return pd.DataFrame(columns=["ticker", "weight"]), 0.0, skipped
    df = pd.DataFrame({"ticker": list(value_by_ticker),
                       "weight": [v / total * 100 for v in value_by_ticker.values()]})
    return df, total, skipped