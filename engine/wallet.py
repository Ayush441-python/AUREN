"""Read-only Base wallet support: find tokenized stocks, native ETH, and major Base assets."""
from __future__ import annotations

import json
import logging
import os
import pathlib
import re
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd
import requests

logger = logging.getLogger("auren-wallet")

API_URL = "https://api.coinbase.com/v1/tokenized-stocks"
TOKEN_CACHE_FILE = pathlib.Path(__file__).parent.parent / "data" / "tokenized_stocks.json"

# High-availability Base RPC failover pool
PRIMARY_BASE_RPC = os.getenv("BASE_RPC_URL", "https://mainnet.base.org")
FALLBACK_BASE_RPCS = [
    PRIMARY_BASE_RPC,
    "https://base.llamarpc.com",
    "https://base-rpc.publicnode.com",
    "https://1rpc.io/base",
    "https://mainnet.base.org",
]
BASE_RPC = PRIMARY_BASE_RPC

BALANCE_OF = "0x70a08231"  # ERC-20 balanceOf(address)
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

# Notable native Base assets
KNOWN_BASE_TOKENS = [
    {
        "symbol": "cbBTC",
        "ticker": "BTC-USD",
        "contract_address": "0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf",
        "decimals": 8,
        "nav_price": 95000.0,
        "multiplier": 1.0,
    },
    {
        "symbol": "USDC",
        "ticker": "USDC",
        "contract_address": "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",
        "decimals": 6,
        "nav_price": 1.0,
        "multiplier": 1.0,
    },
]


def is_valid_address(addr: str) -> bool:
    return bool(ADDRESS_RE.match(addr.strip()))


def underlying_ticker(symbol: str) -> str:
    """NVDAc -> NVDA. Only a label: tokens are identified by contract address."""
    clean = symbol.strip()
    return clean[:-1] if len(clean) > 1 and clean.endswith("c") else clean


def load_bundled_tokens() -> List[Dict[str, Any]]:
    """Load local pre-indexed token registry fallback."""
    if TOKEN_CACHE_FILE.is_file():
        try:
            with open(TOKEN_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error reading bundled token registry: {e}")
    return []


def list_tokenized_stocks(timeout: int = 5) -> List[Dict[str, Any]]:
    """Fetch live tokenized stock metadata with rock-solid fallback to bundled registry."""
    tokens: List[Dict[str, Any]] = []
    page_token = None
    try:
        for _ in range(5):  # safety cap on pages
            params: Dict[str, Any] = {"page_size": 500}
            if page_token:
                params["page_token"] = page_token
            r = requests.get(API_URL, params=params, timeout=timeout)
            if r.status_code == 200:
                data = r.json()
                tokens += data.get("tokens", [])
                page_token = data.get("next_page_token")
                if not page_token:
                    break
            else:
                break
        if tokens:
            try:
                TOKEN_CACHE_FILE.write_text(json.dumps(tokens, indent=2), encoding="utf-8")
            except Exception:
                pass
            return tokens
    except Exception as e:
        logger.info(f"Coinbase API unreachable ({e}); using bundled token registry fallback.")

    bundled = load_bundled_tokens()
    return bundled if bundled else tokens


def _rpc_post_with_failover(payload: Any, rpc_urls: List[str], timeout: int = 15) -> Any:
    """Attempt JSON-RPC call against prioritized list of RPC nodes."""
    last_err: Optional[Exception] = None
    # Deduplicate while preserving order
    seen = set()
    unique_rpcs = [u for u in rpc_urls if u and not (u in seen or seen.add(u))]

    for rpc in unique_rpcs:
        try:
            r = requests.post(rpc, json=payload, timeout=timeout)
            if r.status_code == 200:
                resp = r.json()
                if isinstance(resp, dict) and resp.get("error"):
                    # Check for throttling message
                    err_msg = str(resp["error"])
                    if "429" in err_msg or "rate" in err_msg.lower() or "limit" in err_msg.lower():
                        continue
                return resp
        except Exception as e:
            last_err = e
            continue

    if last_err:
        raise RuntimeError(f"All Base RPC nodes failed. Last error: {last_err}")
    raise RuntimeError("All Base RPC nodes failed to respond.")


def get_native_eth_balance(wallet: str, rpc_urls: List[str] = FALLBACK_BASE_RPCS) -> float:
    """Fetch native Base ETH balance using eth_getBalance with failover."""
    clean_wallet = wallet.strip().lower()
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_getBalance",
        "params": [clean_wallet, "latest"],
    }
    try:
        resp = _rpc_post_with_failover(payload, rpc_urls)
        result = resp.get("result")
        if result and result != "0x":
            raw = int(result, 16)
            return raw / 10**18
    except Exception as e:
        logger.warning(f"Error fetching native ETH balance: {e}")
    return 0.0


def token_balances(
    wallet: str,
    tokens: List[Dict[str, Any]],
    rpc_url: Optional[str] = None,
    chunk: int = 50,
    timeout: int = 20,
) -> Dict[str, float]:
    """Return {contract_address_lowercase: balance in token units} using RPC failover pool."""
    rpc_pool = [rpc_url] + FALLBACK_BASE_RPCS if rpc_url else FALLBACK_BASE_RPCS
    call_data = BALANCE_OF + wallet.strip().lower().removeprefix("0x").rjust(64, "0")
    out: Dict[str, float] = {}

    for i in range(0, len(tokens), chunk):
        part = tokens[i : i + chunk]
        payload = [
            {
                "jsonrpc": "2.0",
                "id": j,
                "method": "eth_call",
                "params": [{"to": t["contract_address"], "data": call_data}, "latest"],
            }
            for j, t in enumerate(part)
        ]
        try:
            resp = _rpc_post_with_failover(payload, rpc_pool, timeout=timeout)
        except Exception as e:
            logger.error(f"Failed RPC batch: {e}")
            continue

        if isinstance(resp, list):
            for item in resp:
                result = item.get("result")
                if not result or result == "0x":
                    continue
                try:
                    raw = int(result, 16)
                    if raw > 0:
                        t = part[item["id"]]
                        out[t["contract_address"].lower()] = raw / 10 ** int(t.get("decimals", 18))
                except Exception:
                    pass
    return out


def get_native_eth_price() -> Tuple[float, Optional[str]]:
    """Retrieve the latest dated market price for ETH-USD from data/prices.csv,
    falling back to a $3,300 estimate if unavailable."""
    prices_file = pathlib.Path(__file__).parent.parent / "data" / "prices.csv"
    if prices_file.exists():
        try:
            df = pd.read_csv(prices_file, usecols=["Date", "ETH-USD"])
            valid = df.dropna(subset=["ETH-USD"])
            if not valid.empty:
                last_row = valid.iloc[-1]
                return float(last_row["ETH-USD"]), str(last_row["Date"])
        except Exception as e:
            logger.warning(f"Failed to read ETH price from prices.csv: {e}")
    return 3300.0, None


def wallet_holdings(
    wallet: str, supported: Set[str], rpc_url: Optional[str] = None
) -> Dict[str, Any]:
    """Inspect Base address for tokenized stocks, cbBTC, USDC, and native ETH."""
    rpc_pool = [rpc_url] + FALLBACK_BASE_RPCS if rpc_url else FALLBACK_BASE_RPCS
    tokens = list_tokenized_stocks()

    # Include known Base crypto tokens in the check list
    all_tokens_to_check = tokens + KNOWN_BASE_TOKENS
    balances = token_balances(wallet, all_tokens_to_check, rpc_url=rpc_pool[0])

    by_addr = {t["contract_address"].lower(): t for t in all_tokens_to_check}
    rows: List[Dict[str, Any]] = []

    for addr, amount in balances.items():
        t = by_addr.get(addr)
        if not t:
            continue
        symbol = t.get("symbol", "?")
        ticker = t.get("ticker") or underlying_ticker(symbol)
        price = float(t.get("nav_price") or 0.0)
        multiplier = float(t.get("multiplier") or 1.0)
        rows.append(
            {
                "token": symbol,
                "ticker": ticker,
                "address": addr,
                "tokens": round(amount, 6),
                "shares": round(amount * multiplier, 6),
                "price": price,
                "value": round(amount * price, 2),
                "supported": ticker in supported,
                "nav_updated": t.get("nav_price_updated_at"),
            }
        )

    # Check native ETH balance
    eth_balance = get_native_eth_balance(wallet, rpc_pool)
    if eth_balance >= 0.0005:  # meaningful dust threshold (~$1.50)
        eth_price, eth_updated = get_native_eth_price()
        rows.append(
            {
                "token": "ETH",
                "ticker": "ETH-USD",
                "address": "native-base",
                "tokens": round(eth_balance, 6),
                "shares": round(eth_balance, 6),
                "price": eth_price,
                "value": round(eth_balance * eth_price, 2),
                "supported": "ETH-USD" in supported,
                "nav_updated": eth_updated,
            }
        )

    rows.sort(key=lambda r: r["value"], reverse=True)
    return {"rows": rows, "n_tokens": len(all_tokens_to_check)}


def holdings_to_portfolio(
    rows: List[Dict[str, Any]]
) -> Tuple[pd.DataFrame, float, List[Dict[str, Any]]]:
    """Aggregate supported holdings by underlying ticker.
    Returns (portfolio_df with ticker + weight %, total_value, skipped_rows)."""
    value_by_ticker: Dict[str, float] = {}
    skipped: List[Dict[str, Any]] = []

    for r in rows:
        if r.get("supported") and r.get("value", 0) > 0:
            ticker = r["ticker"]
            value_by_ticker[ticker] = value_by_ticker.get(ticker, 0.0) + r["value"]
        else:
            skipped.append(r)

    total = sum(value_by_ticker.values())
    if total <= 0:
        return pd.DataFrame(columns=["ticker", "weight"]), 0.0, skipped

    df = pd.DataFrame(
        {
            "ticker": list(value_by_ticker.keys()),
            "weight": [v / total * 100 for v in value_by_ticker.values()],
        }
    )
    return df, total, skipped
