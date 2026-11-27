"""Universe of supported tickers, sectors, and broad risk groups."""
from __future__ import annotations

import logging
from typing import Dict, List, Tuple

logger = logging.getLogger("auren-universe")

# Industry label for each ticker (what the company does).
SECTORS: Dict[str, str] = {
    # Big Tech
    "NVDA": "Semiconductors",
    "MSFT": "Software",
    "AAPL": "Consumer Technology",
    "GOOGL": "Internet & AI",
    "GOOG": "Internet & AI",
    "AMZN": "E-Commerce & Cloud",
    "META": "Social Media",
    "AVGO": "Semiconductors",
    "ORCL": "Software & Cloud",
    "NFLX": "Entertainment",

    # AI & Semiconductors
    "AMD": "Semiconductors",
    "INTC": "Semiconductors",
    "QCOM": "Semiconductors",
    "MU": "Memory Chips",
    "ARM": "Semiconductors",
    "TSM": "Semiconductors",
    "ASML": "Semiconductor Equipment",
    "AMAT": "Semiconductor Equipment",
    "LRCX": "Semiconductor Equipment",
    "ADI": "Semiconductors",
    "MRVL": "Semiconductors",
    "TXN": "Semiconductors",

    # Software & Cybersecurity
    "PLTR": "AI & Data Analytics",
    "ADBE": "Software",
    "CRM": "Software",
    "PANW": "Cybersecurity",
    "CRWD": "Cybersecurity",
    "SNPS": "Software & Semiconductors",
    "NOW": "Enterprise Software",
    "WDAY": "Enterprise Software",
    "INTU": "Financial Software",
    "ADSK": "Engineering Software",

    # Internet & Communication
    "CSCO": "Networking",
    "TMUS": "Telecommunications",
    "SHOP": "E-Commerce",
    "ABNB": "Travel & Hospitality",
    "PYPL": "Digital Payments",
    "MELI": "E-Commerce & Fintech",
    "BABA": "E-Commerce & Cloud",

    # Consumer & Retail
    "TSLA": "Automotive",
    "COST": "Retail",
    "WMT": "Retail",
    "SBUX": "Restaurants",
    "PEP": "Consumer Staples",
    "MDLZ": "Consumer Staples",
    "PG": "Consumer Staples",
    "DIS": "Entertainment",

    # Healthcare & Biotechnology
    "AMGN": "Biotechnology",
    "GILD": "Biotechnology",
    "VRTX": "Biotechnology",
    "REGN": "Biotechnology",
    "ISRG": "Medical Devices",
    "ALNY": "Biotechnology",
    "JNJ": "Pharmaceuticals",

    # Industrial & Energy
    "HON": "Industrials",
    "ODFL": "Transportation",
    "PCAR": "Automotive Manufacturing",
    "XEL": "Utilities",
    "AEP": "Utilities",
    "XOM": "Oil & Gas",
    "CVX": "Oil & Gas",

    # Financials & Payments
    "JPM": "Banks",
    "V": "Digital Payments",
    "MA": "Digital Payments",
    "BAC": "Banks",
    "GS": "Investment Banking",

    # Major ETFs & Indices
    "SPY": "S&P 500 Index ETF",
    "QQQ": "Nasdaq 100 Index ETF",
    "IWM": "Russell 2000 ETF",
    "DIA": "Dow Jones ETF",
    "VOO": "S&P 500 ETF",
    "VTI": "Total Stock Market ETF",
    "TLT": "20+ Year Treasury Bond ETF",
    "BND": "Total Bond Market ETF",
    "XLF": "Financial Select Sector ETF",
    "XLK": "Technology Select Sector ETF",
    "XLE": "Energy Select Sector ETF",

    # Commodities & Gold
    "GLD": "Gold",
    "IAU": "Gold",
    "SLV": "Silver",

    # Crypto & Digital Assets
    "ETH-USD": "Crypto",
    "BTC-USD": "Crypto",
    "SOL-USD": "Crypto",
    "AVAX-USD": "Crypto",
    "DOGE-USD": "Crypto",
    "LINK-USD": "Crypto",
    "SUI-USD": "Crypto",
    "COIN": "Crypto Exchange",
    "MSTR": "Bitcoin Treasury",
    "USDC": "Stablecoin",
}

# Broad group for each ticker.
_GROUP_MEMBERS: Dict[str, List[str]] = {
    "Big Tech": [
        "NVDA", "MSFT", "AAPL", "GOOGL", "GOOG", "AMZN", "META",
        "AVGO", "ORCL", "NFLX"
    ],
    "AI & Semiconductors": [
        "AMD", "INTC", "QCOM", "MU", "ARM", "TSM", "ASML",
        "AMAT", "LRCX", "ADI", "MRVL", "TXN"
    ],
    "Software & Cybersecurity": [
        "PLTR", "ADBE", "CRM", "PANW", "CRWD", "SNPS",
        "NOW", "WDAY", "INTU", "ADSK"
    ],
    "Internet & Communication": [
        "CSCO", "TMUS", "SHOP", "ABNB", "PYPL", "MELI", "BABA"
    ],
    "Consumer & Retail": [
        "TSLA", "COST", "WMT", "SBUX", "PEP", "MDLZ", "PG", "DIS"
    ],
    "Healthcare & Biotechnology": [
        "AMGN", "GILD", "VRTX", "REGN", "ISRG", "ALNY", "JNJ"
    ],
    "Industrial & Energy": [
        "HON", "ODFL", "PCAR", "XEL", "AEP", "XOM", "CVX", "XLE"
    ],
    "Financials": [
        "JPM", "V", "MA", "BAC", "GS", "XLF"
    ],
    "Broad Market ETFs": [
        "SPY", "QQQ", "IWM", "DIA", "VOO", "VTI", "XLK"
    ],
    "Bonds & Fixed Income": [
        "TLT", "BND"
    ],
    "Gold & Commodities": [
        "GLD", "IAU", "SLV"
    ],
    "Crypto": [
        "ETH-USD", "BTC-USD", "SOL-USD", "AVAX-USD", "DOGE-USD",
        "LINK-USD", "SUI-USD", "COIN", "MSTR"
    ],
    "Cash & Stablecoins": [
        "USDC"
    ],
}

GROUPS: Dict[str, str] = {t: g for g, members in _GROUP_MEMBERS.items() for t in members}

# Ensure static synchronization
_mismatch = set(SECTORS) ^ set(GROUPS)
if _mismatch:
    raise ValueError(f"Tickers missing from SECTORS or GROUPS: {sorted(_mismatch)}")


def classify_and_register_ticker(ticker: str) -> Tuple[str, str]:
    """Dynamically classify and register any new ticker on the fly."""
    t = ticker.strip().upper()
    if t in SECTORS and t in GROUPS:
        return SECTORS[t], GROUPS[t]

    # Deterministic heuristics
    sector = "General Equities"
    group = "General Equities"

    if t.endswith("-USD") or t in {"BTC", "ETH", "SOL", "DOGE", "AVAX", "CBBTC"}:
        sector = "Crypto"
        group = "Crypto"
    elif t in {"USDC", "USDT", "DAI", "USD", "BUSD"}:
        sector = "Stablecoin"
        group = "Cash & Stablecoins"
    elif t in {"SPY", "QQQ", "IWM", "DIA", "VOO", "VTI", "IVV"}:
        sector = "Index ETF"
        group = "Broad Market ETFs"
    elif t in {"TLT", "BND", "AGG", "IEF", "SHY"}:
        sector = "Fixed Income"
        group = "Bonds & Fixed Income"
    elif t in {"GLD", "SLV", "USO", "UNG"}:
        sector = "Commodities"
        group = "Gold & Commodities"
    else:
        try:
            import yfinance as yf
            info = yf.Ticker(t).info
            sec = info.get("sector")
            ind = info.get("industry")
            if sec:
                sector = ind or sec
                sec_lower = sec.lower()
                ind_lower = str(ind).lower()
                if "semiconductor" in ind_lower or "chip" in ind_lower:
                    group = "AI & Semiconductors"
                elif "technology" in sec_lower or "software" in sec_lower:
                    group = "Big Tech"
                elif "healthcare" in sec_lower or "biotech" in ind_lower:
                    group = "Healthcare & Biotechnology"
                elif "financial" in sec_lower or "bank" in ind_lower:
                    group = "Financials"
                elif "consumer" in sec_lower or "retail" in ind_lower:
                    group = "Consumer & Retail"
                elif "communication" in sec_lower or "media" in ind_lower:
                    group = "Internet & Communication"
                elif "energy" in sec_lower or "utilities" in sec_lower or "industrial" in sec_lower:
                    group = "Industrial & Energy"
                else:
                    group = sec
        except Exception as e:
            logger.info(f"Could not auto-fetch metadata for ticker {t}: {e}")

    SECTORS[t] = sector
    GROUPS[t] = group
    return sector, group
