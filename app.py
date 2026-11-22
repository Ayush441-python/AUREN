import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from engine.data import load_prices, load_volumes
from engine.env import load_env, setting
from engine.liquidity import avg_daily_value, days_to_exit
from engine.metrics import (concentration, portfolio_returns, volatility,
                            max_drawdown, correlation, high_pairs, sector_exposure)
from engine.report import ai_report, unverified_numbers
from engine.score import risk_score, RULE_TABLE
from engine.stress import SCENARIOS, stress, worst_periods
from engine.universe import GROUPS, SECTORS
from engine.wallet import (BASE_RPC, is_valid_address, wallet_holdings,
                           holdings_to_portfolio)

load_env()  # .env locally; Streamlit Cloud uses Secrets

st.set_page_config(
    page_title="AUREN · See the risk before it sees you",
    page_icon="◐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------------ brand & styles
GOLD, GREY, PANEL, BG = "#E3B341", "#8A8F98", "#18181B", "#0E0E10"
TEXT, GRID = "#F5F6F7", "#26262B"
DANGER, SUCCESS, WARN = "#F87171", "#4ADE80", "#FBBF24"
ASSET_GREYS = ["#5B5F68", "#7A7F88", "#A3A7AF", "#C9CCD2", "#E1E3E6", "#44474F"]

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&display=swap');

html, body, .stApp, [data-testid="stMarkdownContainer"], button, input {
    font-family: 'Inter', sans-serif;
}
.stApp { background: #0E0E10; }
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 1.8rem; padding-bottom: 3rem; max-width: 1240px; }
section[data-testid="stSidebar"] { background: #121215; border-right: 1px solid #26262B; }

.wordmark { font-weight: 700; letter-spacing: 0.38em; font-size: 2.1rem;
            color: #F5F6F7; line-height: 1; }
.wordmark .ring { color: #E3B341; margin-right: 0.55rem; letter-spacing: 0; }
.wordmark.small { font-size: 1.15rem; margin-bottom: 1.2rem; }
.tagline { color: #8A8F98; margin-top: 0.6rem; font-size: 1.02rem; }

.section-title { font-size: 1.08rem; font-weight: 600; color: #F5F6F7;
                 margin: 1.4rem 0 0.2rem 0; }
.section-sub { color: #8A8F98; font-size: 0.88rem; margin-bottom: 0.75rem; }

.card { background: #18181B; border: 1px solid #26262B; border-radius: 14px;
        padding: 16px 18px; hei
</style>
"""

# (The rest of the original app layout code remains unchanged until the liquidity tab.)

with st.container():
    # ... other tabs and UI elements ...
    pass

# ------------------------------------------------------------------ Liquidity tab
with st.container():
    # Assuming the portfolio weights, positions, and ADV have been computed earlier
    # pos_values: pd.Series of dollar holdings per ticker
    # adv: pd.Series of average daily dollar volume per ticker
    # weights: pd.Series of portfolio weights (not used directly here)
    dte = days_to_exit(pos_values, adv, participation=0.10)

    lq1, lq2, lq3 = st.columns(3)
    blocked = dte.eq(float("inf"))
    incomplete = dte.isna().any() or dte.empty
    all_under_one_day = False
    if blocked.any():
        blocked_tickers = ", ".join(dte.index[blocked])
        max_display, detail = "No finite exit", blocked_tickers
        notice = f"Zero modeled trading capacity for <b>{blocked_tickers}</b>. These holdings cannot be sold at the current volume cap."
    elif incomplete:
        max_display, detail = "Unknown", "Missing volume data"
        notice = "Volume data is unavailable for a holding. The full portfolio's exit time is unknown."
    else:
        slowest = dte.idxmax()
        max_days = dte.at[slowest]
        max_display, detail = f"{max_days:.2f} days", f"Holding: {slowest}"
        all_under_one_day = max_days < 1
        if all_under_one_day:
            notice = "✓ All portfolio positions can be fully liquidated in under 1 trading day at 10% volume participation."
        else:
            notice = f"<b>Liquidity Notice:</b> Liquidating <b>{slowest}</b> would require at least 1 trading day ({max_days:.2f} days) at 10% volume participation."
    lq1.markdown(card("Max days to exit", max_display, detail), unsafe_allow_html=True)
    lq2.markdown(card("Participation rate", "10%", "Standard conservative liquidation cap"), unsafe_allow_html=True)
    lq3.markdown(card("30D average volume", "Incomplete" if incomplete else "Active", "Computed over last 30 trading sessions", gold=True), unsafe_allow_html=True)

    liq_rows = []
    for t in weights.index:
        v_daily = adv.get(t, float("nan"))
        days = dte.get(t, float("nan"))
        pos_val = pos_values[t]
        if pd.isna(days):
            status = "Unknown (missing volume)"
        elif days == float("inf"):
            status = "No trading capacity"
        else:
            status = "Instant (<0.1d)" if days < 0.1 else "Liquid (<1d)" if days < 1.0 else "Illiquid (1d+)"
        liq_rows.append({
            "Ticker": t,
            "Position ($)": pos_val,
            "30D Daily Traded ($)": v_daily,
            "10% Cap ($/day)": v_daily * 0.10 if pd.notna(v_daily) else float("nan"),
            "Days to Exit": days,
            "Liquidity Status": status
        })
    liq_df = pd.DataFrame(liq_rows)

    st.dataframe(liq_df.style.apply(highlight_slowest, axis=1), use_container_width=True)

    st.markdown(callout(notice, muted=all_under_one_day, danger=not all_under_one_day), unsafe_allow_html=True)

    st.caption("Volume data from Yahoo Finance. Crypto volumes are USD-denominated. Past trading volume may dry up during crises.")

# (Rest of the app continues...)