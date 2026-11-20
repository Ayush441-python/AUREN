# Industry label for each ticker (what the company does).
SECTORS = {
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

    # Consumer & Retail
    "TSLA": "Automotive",
    "COST": "Retail",
    "WMT": "Retail",
    "SBUX": "Restaurants",
    "PEP": "Consumer Staples",
    "MDLZ": "Consumer Staples",

    # Healthcare & Biotechnology
    "AMGN": "Biotechnology",
    "GILD": "Biotechnology",
    "VRTX": "Biotechnology",
    "REGN": "Biotechnology",
    "ISRG": "Medical Devices",
    "ALNY": "Biotechnology",

    # Industrial & Energy
    "HON": "Industrials",
    "ODFL": "Transportation",
    "PCAR": "Automotive Manufacturing",
    "XEL": "Utilities",
    "AEP": "Utilities",

    # Added back so the playbook's default portfolio and scenarios keep working.
    # Delete these five lines (and their entries below) if you don't want them.
    "ETH-USD": "Crypto",
    "BTC-USD": "Crypto",
    "GLD": "Gold",
    "JPM": "Banks",
    "XOM": "Oil & Gas",
}

# Broad group for each ticker. The risk score, stress tests and hidden-bet
# warnings use these, so "NVDA + MSFT + GOOGL" counts as one Big Tech bet.
_GROUP_MEMBERS = {
    "Big Tech": ["NVDA", "MSFT", "AAPL", "GOOGL", "GOOG", "AMZN", "META",
                 "AVGO", "ORCL", "NFLX"],
    "AI & Semiconductors": ["AMD", "INTC", "QCOM", "MU", "ARM", "TSM", "ASML",
                            "AMAT", "LRCX", "ADI", "MRVL", "TXN"],
    "Software & Cybersecurity": ["PLTR", "ADBE", "CRM", "PANW", "CRWD", "SNPS",
                                 "NOW", "WDAY", "INTU", "ADSK"],
    "Internet & Communication": ["CSCO", "TMUS", "SHOP", "ABNB", "PYPL", "MELI"],
    "Consumer & Retail": ["TSLA", "COST", "WMT", "SBUX", "PEP", "MDLZ"],
    "Healthcare & Biotechnology": ["AMGN", "GILD", "VRTX", "REGN", "ISRG", "ALNY"],
    "Industrial & Energy": ["HON", "ODFL", "PCAR", "XEL", "AEP", "XOM"],
    "Crypto": ["ETH-USD", "BTC-USD"],
    "Gold": ["GLD"],
    "Financials": ["JPM"],
}
GROUPS = {t: g for g, members in _GROUP_MEMBERS.items() for t in members}

_mismatch = set(SECTORS) ^ set(GROUPS)
if _mismatch:
    raise ValueError(f"Tickers missing from SECTORS or GROUPS: {sorted(_mismatch)}")