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
}

# Broad risk groups mapping sector/industry keywords to macro categories.
GROUPS: List[Tuple[str, List[str]]] = [
    (
        "AI & Semiconductors",
        [
            "Semiconductors",
            "Semiconductor Equipment",
            "Memory Chips",
            "AI & Data Analytics",
        ],
    ),
    (
        "Big Tech & Cloud",
        [
            "Software",
            "Consumer Technology",
            "Internet & AI",
            "E-Commerce & Cloud",
            "Social Media",
            "Software & Cloud",
            "Software & Semiconductors",
            "Enterprise Software",
        ],
    ),
    (
        "Cybersecurity & Infrastructure",
        [
            "Cybersecurity",
            "Networking",
            "Telecommunications",
            "Engineering Software",
        ],
    ),
    (
        "Consumer, Retail & Entertainment",
        [
            "Entertainment",
            "E-Commerce",
            "Travel & Hospitality",
            "Automotive",
            "Retail",
            "Restaurants",
            "Consumer Staples",
        ],
    ),
    (
        "Financials, Payments & Real Estate",
        [
            "Financial Software",
            "Digital Payments",
            "E-Commerce & Fintech",
            "Banks",
            "Investment Banking",
            "Financial Select Sector ETF",
        ],
    ),
    (
        "Healthcare & Biotech",
        [
            "Biotechnology",
            "Medical Devices",
            "Pharmaceuticals",
        ],
    ),
    (
        "Industrials, Energy & Utilities",
        [
            "Industrials",
            "Transportation",
            "Automotive Manufacturing",
            "Utilities",
            "Oil & Gas",
            "Energy Select Sector ETF",
        ],
    ),
    (
        "Broad Market Indices & ETFs",
        [
            "S&P 500 Index ETF",
            "Nasdaq 100 Index ETF",
            "Russell 2000 ETF",
            "Dow Jones ETF",
            "S&P 500 ETF",
            "Total Stock Market ETF",
            "20+ Year Treasury Bond ETF",
            "Total Bond Market ETF",
            "Technology Select Sector ETF",
        ],
    ),
    (
        "Commodities, Crypto & Alternatives",
        [
            "Gold",
            "Silver",
            "Crypto",
            "Crypto Exchange",
        ],
    ),
]


def get_sector(ticker: str, metadata_provider=None) -> str:
    """Resolve the sector for a given ticker, querying the metadata provider if unknown."""
    if ticker in SECTORS:
        return SECTORS[ticker]

    if metadata_provider is not None:
        try:
            meta = metadata_provider.fetch(ticker)
            if meta and hasattr(meta, "info") and meta.info:
                sector = meta.info.get("sector")
                industry = meta.info.get("industry")
                if industry:
                    SECTORS[ticker] = industry
                    return industry
                if sector:
                    SECTORS[ticker] = sector
                    return sector
        except Exception as e:
            logger.warning(f"Failed to fetch metadata for {ticker}: {e}")

    return "General Equities"


def get_group(sector_or_industry: str) -> str:
    """Map a sector or industry label to a broad risk group."""
    for group_name, keywords in GROUPS:
        for kw in keywords:
            if kw.lower() in sector_or_industry.lower():
                return group_name
    return "General Equities"


def classify_ticker(ticker: str, metadata_provider=None) -> str:
    """Classify a ticker into its broad risk group."""
    sector = get_sector(ticker, metadata_provider)
    return get_group(sector)