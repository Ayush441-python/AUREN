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

from engine.data import get_latest_prices

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
    "https://developer-access-mainnet.base.org",
    "https://mainnet.base.org",
]
BASE_RPC = PRIMARY_BASE_RPC

BALANCE_OF = "0x70a08231"  # ERC-20 balanceOf(address)
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

# Notable native Base ecosystem assets
KNOWN_BASE_TOKENS = [
    {
        "symbol": "cbBTC",
        "ticker": "BTC-USD",
        "contract_address": "0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf",
        "decimals": 8,
        "nav_price": 65000.0,
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
    {
        "symbol": "WETH",
        "ticker": "ETH-USD",
        "contract_address": "0x4200000000000000000000000000000000000006",
        "decimals": 18,
        "nav_price": 1850.0,
        "multiplier": 1.0,
    },
    {
        "symbol": "AERO",
        "ticker": "AERO-USD",
        "contract_address": "0x940181a94a35a4569e4529a3cdfb74e38fd98631",
        "decimals": 18,
        "nav_price": 1.45,
        "multiplier": 1.0,
    },
    {
        "symbol": "VIRTUAL",
        "ticker": "VIRTUAL-USD",
        "contract_address": "0x0b3e328455c4059eeb9e3f84b5543f74e24e7e1b",
        "decimals": 18,
        "nav_price": 2.85,
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
                        addr_lower = str(t["contract_address"]).lower()
                        default_dec = 8 if addr_lower.startswith("0xb20") else 18
                        decimals = int(t.get("decimals", default_dec))
                        out[addr_lower] = raw / (10 ** decimals)
                except Exception:
                    pass
    return out


def wallet_holdings(
    wallet: str, supported: Set[str], rpc_url: Optional[str] = None
) -> Dict[str, Any]:
    """Inspect Base address for B20 tokenized stocks, cbBTC, USDC, WETH, AERO, VIRTUAL, and native ETH."""
    rpc_pool = [rpc_url] + FALLBACK_BASE_RPCS if rpc_url else FALLBACK_BASE_RPCS
    tokens = list_tokenized_stocks()

    # Include known Base crypto tokens in the check list
    all_tokens_to_check = tokens + KNOWN_BASE_TOKENS
    balances = token_balances(wallet, all_tokens_to_check, rpc_url=rpc_pool[0])

    by_addr = {t["contract_address"].lower(): t for t in all_tokens_to_check}

    # Gather needed tickers to resolve dynamic prices from the pricing engine cache
    needed_tickers = ["ETH-USD", "BTC-USD"]
    for addr in balances:
        t = by_addr.get(addr)
        if t:
            tk = t.get("ticker") or underlying_ticker(t.get("symbol", ""))
            if tk:
                needed_tickers.append(tk)

    live_prices, price_ts = get_latest_prices(needed_tickers)

    rows: List[Dict[str, Any]] = []

    for addr, amount in balances.items():
        t = by_addr.get(addr)
        if not t:
            continue
        symbol = t.get("symbol", "?")
        ticker = t.get("ticker") or underlying_ticker(symbol)
        # Prefer dynamic cached price from pricing engine, falling back to token nav_price
        price = float(live_prices.get(ticker) or t.get("nav_price") or 0.0)
        multiplier = float(t.get("multiplier") or 1.0)
        shares = round(amount * multiplier, 6)
        rows.append(
            {
                "token": symbol,
                "ticker": ticker,
                "address": addr,
                "tokens": round(amount, 6),
                "shares": shares,
                "price": price,
                "value": round(shares * price, 2),
                "supported": ticker in supported,
                "nav_updated": price_ts or t.get("nav_price_updated_at"),
            }
        )

    # Check native ETH balance with dynamic cached price from pricing engine
    eth_balance = get_native_eth_balance(wallet, rpc_pool)
    if eth_balance >= 0.0005:  # meaningful dust threshold
        eth_price = float(live_prices.get("ETH-USD") or 1850.0)
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
                "nav_updated": price_ts,
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


ERC8021_MARKER = "80218021802180218021802180218021"


def encode_erc8021_suffix(builder_code: str) -> str:
    """Encode Base Builder Code(s) into standard ERC-8021 Schema 0 calldata suffix hex (without 0x)."""
    clean_code = builder_code.strip()
    if not clean_code:
        return ""
    code_bytes = clean_code.encode("ascii")
    if len(code_bytes) > 255:
        raise ValueError("Builder code exceeds 255 bytes")
    return f"{code_bytes.hex()}{len(code_bytes):02x}00{ERC8021_MARKER}"


def encode_risk_attestation_calldata(
    score: int,
    level: str,
    top_asset: str,
    portfolio_name: str = "Portfolio",
    builder_code: str = "bc_auren",
    timestamp: int | None = None,
) -> Dict[str, Any]:
    """Build deterministic Base Mainnet risk attestation calldata with ERC-8021 Builder Code suffix."""
    import hashlib
    import time

    ts = timestamp if timestamp is not None else int(time.time())
    p_hash = hashlib.sha256(f"{portfolio_name}:{score}:{level}:{top_asset}".encode("utf-8")).hexdigest()[:16]
    payload_str = (
        f"AUREN_AUDIT_V1|score={int(score)}|level={level}|top={top_asset}"
        f"|hash={p_hash}|ts={ts}"
    )
    payload_hex = payload_str.encode("utf-8").hex()
    suffix_hex = encode_erc8021_suffix(builder_code)
    full_data = f"0x{payload_hex}{suffix_hex}"

    return {
        "chain_id": 8453,
        "chain_id_hex": "0x2105",
        "network": "Base Mainnet",
        "payload_text": payload_str,
        "payload_hex": f"0x{payload_hex}",
        "builder_code": builder_code.strip(),
        "erc8021_suffix": f"0x{suffix_hex}" if suffix_hex else None,
        "calldata": full_data,
        "estimated_gas": 24000,
    }


def decode_erc8021_calldata(calldata_hex: str) -> Dict[str, Any]:
    """Decode an on-chain Base transaction input containing AUREN audit payload and ERC-8021 suffix."""
    raw = calldata_hex.strip().lower().removeprefix("0x")
    has_marker = raw.endswith(ERC8021_MARKER)
    builder_code: Optional[str] = None
    payload_hex = raw

    if has_marker and len(raw) >= 36:
        without_marker = raw[:-32]
        schema_id = without_marker[-2:]
        len_hex = without_marker[-4:-2]
        if schema_id == "00":
            code_len = int(len_hex, 16)
            code_hex_chars = code_len * 2
            body = without_marker[:-4]
            if len(body) >= code_hex_chars:
                code_hex = body[-code_hex_chars:] if code_hex_chars > 0 else ""
                builder_code = bytes.fromhex(code_hex).decode("ascii", errors="replace")
                payload_hex = body[:-code_hex_chars] if code_hex_chars > 0 else body

    try:
        payload_text = bytes.fromhex(payload_hex).decode("utf-8", errors="replace")
    except Exception:
        payload_text = ""

    return {
        "erc8021_verified": bool(builder_code),
        "builder_code": builder_code,
        "payload_text": payload_text,
        "is_auren_audit": payload_text.startswith("AUREN_AUDIT_V1|"),
    }

