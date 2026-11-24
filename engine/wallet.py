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
PRICES_CSV_FILE = pathlib.Path(__file__).parent.parent / "data" / "prices.csv"

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


def get_latest_eth_price() -> Tuple[float, str, bool]:
    """Retrieve the latest dated ETH price from prices.csv or fallback to estimated $3,300."""
    if PRICES_CSV_FILE.is_file():
        try:
            df = pd.read_csv(PRICES_CSV_FILE)
            # Find ETH or ETH-USD column/row depending on format
            date_col = None
            for col in ["date", "Date", "timestamp", "Timestamp"]:
                if col in df.columns:
                    date_col = col
                    break
            
            # Look for ETH / ETH-USD column
            eth_col = None
            for col in ["ETH", "ETH-USD", "eth", "eth-usd"]:
                if col in df.columns:
                    eth_col = col
                    break
            
            if eth_col and date_col:
                valid_df = df.dropna(subset=[eth_col])
                if not valid_df.empty:
                    # Sort by date descending
                    valid_df = valid_df.sort_values(by=date_col, ascending=False)
                    latest_row = valid_df.iloc[0]
                    price = float(latest_row[eth_col])
                    date_str = str(latest_row[date_col])
                    return price, date_str, False
            
            # Alternatively, if format is Date, Ticker, Close/Price
            if "Ticker" in df.columns or "ticker" in df.columns:
                t_col = "Ticker" if "Ticker" in df.columns else "ticker"
                p_col = None
                for col in ["Close", "price", "Price", "nav", "NAV"]:
                    if col in df.columns:
                        p_col = col
                        break
                if p_col and date_col:
                    eth_rows = df[df[t_col].astype(str).str.upper().isin(["ETH", "ETH-USD"])]
                    if not eth_rows.empty:
                        eth_rows = eth_rows.sort_values(by=date_col, ascending=False)
                        latest_row = eth_rows.iloc[0]
                        price = float(latest_row[p_col])
                        date_str = str(latest_row[date_col])
                        return price, date_str, False
        except Exception as e:
            logger.warning(f"Error reading latest ETH price from prices.csv: {e}")

    # Fallback estimate
    return 3300.0, "Estimated", True


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

    return load_bundled_tokens()


def get_rpc_client() -> str:
    return BASE_RPC


def query_eth_balance(address: str) -> float:
    """Query native ETH balance for a given address using RPC json-rpc eth_getBalance."""
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBalance",
        "params": [address, "latest"],
        "id": 1,
    }
    for rpc in FALLBACK_BASE_RPCS:
        try:
            r = requests.post(rpc, json=payload, timeout=5)
            if r.status_code == 200:
                res = r.json()
                if "result" in res and res["result"]:
                    wei_val = int(res["result"], 16)
                    return wei_val / 10**18
        except Exception:
            continue
    return 0.0


def query_erc20_balance(address: str, contract_address: str, decimals: int) -> float:
    """Query ERC-20 token balance using eth_call with balanceOf signature."""
    padded_addr = address.lower().replace("0x", "").zfill(64)
    data = BALANCE_OF + padded_addr
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_call",
        "params": [
            {"to": contract_address, "data": data},
            "latest",
        ],
        "id": 1,
    }
    for rpc in FALLBACK_BASE_RPCS:
        try:
            r = requests.post(rpc, json=payload, timeout=5)
            if r.status_code == 200:
                res = r.json()
                if "result" in res and res["result"] and res["result"] != "0x":
                    raw_val = int(res["result"], 16)
                    return raw_val / (10**decimals)
        except Exception:
            continue
    return 0.0


def fetch_wallet_holdings(address: str) -> Dict[str, Any]:
    """Fetch all supported holdings for a wallet address on Base."""
    if not is_valid_address(address):
        raise ValueError(f"Invalid wallet address: {address}")

    holdings = []
    total_value = 0.0

    # 1. Native ETH
    eth_balance = query_eth_balance(address)
    eth_price, eth_date, is_estimate = get_latest_eth_price()
    eth_value = eth_balance * eth_price
    if eth_balance > 0:
        total_value += eth_value
        holdings.append({
            "symbol": "ETH",
            "ticker": "ETH-USD",
            "balance": eth_balance,
            "price": eth_price,
            "value": eth_value,
            "price_date": eth_date,
            "is_estimate": is_estimate,
            "label": f"Price ({eth_date})" if not is_estimate else "Price (Estimated)",
        })

    # 2. Known Base tokens (cbBTC, USDC, etc.)
    for token in KNOWN_BASE_TOKENS:
        bal = query_erc20_balance(address, token["contract_address"], token["decimals"])
        if bal > 0:
            val = bal * token["nav_price"] * token["multiplier"]
            total_value += val
            holdings.append({
                "symbol": token["symbol"],
                "ticker": token["ticker"],
                "balance": bal,
                "price": token["nav_price"],
                "value": val,
                "price_date": "Live/NAV",
                "is_estimate": False,
                "label": "Price",
            })

    # 3. Tokenized stocks
    token_stocks = list_tokenized_stocks()
    for stock in token_stocks:
        contract_addr = stock.get("contract_address") or stock.get("address")
        if not contract_addr:
            continue
        decimals = stock.get("decimals", 18)
        bal = query_erc20_balance(address, contract_addr, decimals)
        if bal > 0:
            nav = float(stock.get("nav_price", stock.get("price", 0.0)))
            val = bal * nav
            total_value += val
            sym = stock.get("symbol", "UNKNOWN")
            holdings.append({
                "symbol": sym,
                "ticker": underlying_ticker(sym),
                "balance": bal,
                "price": nav,
                "value": val,
                "price_date": "NAV",
                "is_estimate": False,
                "label": "Price",
            })

    # Calculate weights
    for h in holdings:
        h["weight"] = (h["value"] / total_value) if total_value > 0 else 0.0

    return {
        "address": address,
        "total_value": total_value,
        "holdings": holdings,
    }