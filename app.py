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
        padding: 16px 18px; height: 100%; display: flex; flex-direction: column; justify-content: space-between; }
.card .label { color: #8A8F98; font-size: 0.74rem; text-transform: uppercase;
               letter-spacing: 0.09em; font-weight: 600; }
.card .value { font-family: 'JetBrains Mono', monospace; font-weight: 700;
               font-size: 1.85rem; color: #F5F6F7; margin: 6px 0 4px 0; }
.card .value.gold { color: #E3B341; }
.card .value.danger { color: #F87171; }
.card .value.success { color: #4ADE80; }
.card .sub { color: #8A8F98; font-size: 0.82rem; line-height: 1.35; }

.callout { border-left: 3px solid #E3B341; background: #18181B;
           border-radius: 8px; padding: 12px 16px; margin: 8px 0;
           color: #F5F6F7; font-size: 0.92rem; }
.callout.muted { border-left-color: #44474F; color: #8A8F98; }
.callout.danger { border-left-color: #F87171; background: rgba(248,113,113,0.06); }

.chip { display: inline-block; padding: 4px 12px; border-radius: 999px;
        font-size: 0.8rem; font-weight: 600;
        font-family: 'JetBrains Mono', monospace; }
.chip.ok { background: rgba(227,179,65,0.14); color: #E3B341; }
.chip.bad { background: rgba(248,113,113,0.16); color: #F87171; }

.badge-low { display: inline-block; padding: 2px 10px; border-radius: 6px; font-weight: 700;
             font-size: 0.85rem; background: rgba(74,222,128,0.15); color: #4ADE80; }
.badge-med { display: inline-block; padding: 2px 10px; border-radius: 6px; font-weight: 700;
             font-size: 0.85rem; background: rgba(251,191,36,0.15); color: #FBBF24; }
.badge-high { display: inline-block; padding: 2px 10px; border-radius: 6px; font-weight: 700;
              font-size: 0.85rem; background: rgba(248,113,113,0.15); color: #F87171; }

.footer { color: #8A8F98; font-size: 0.82rem; margin-top: 2.8rem;
          padding-top: 1.2rem; border-top: 1px solid #26262B; line-height: 1.6; }

button[data-baseweb="tab"] { font-weight: 600; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------- helpers
def card(label: str, value: str, sub: str = "", gold: bool = False, color: str = "") -> str:
    if color:
        cls = f"value {color}"
    elif gold:
        cls = "value gold"
    else:
        cls = "value"
    return (f'<div class="card"><div class="label">{label}</div>'
            f'<div class="{cls}">{value}</div><div class="sub">{sub}</div></div>')


def callout(text: str, muted: bool = False, danger: bool = False) -> str:
    if danger:
        cls = "callout danger"
    elif muted:
        cls = "callout muted"
    else:
        cls = "callout"
    return f'<div class="{cls}">{text}</div>'


def section(title: str, sub: str = ""):
    st.markdown(f'<div class="section-title">{title}</div>'
                f'<div class="section-sub">{sub}</div>', unsafe_allow_html=True)


def style(fig: go.Figure, height: int = 380, title: str | None = None) -> go.Figure:
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=TEXT, size=13),
        margin=dict(l=10, r=10, t=50 if title else 20, b=10),
        legend=dict(orientation="h", y=-0.18, font=dict(color=GREY)),
        hoverlabel=dict(bgcolor=PANEL, font_color=TEXT),
    )
    if title:
        fig.update_layout(title=dict(text=title, x=0,
                                     font=dict(size=15, color=TEXT)))
    fig.update_xaxes(gridcolor=GRID, zeroline=False, showline=False, color=GREY)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, showline=False, color=GREY)
    return fig


@st.cache_data(ttl=3600, show_spinner="Loading 2 years of prices…")
def get_prices(tickers: tuple) -> pd.DataFrame:
    return load_prices(list(tickers))


@st.cache_data(ttl=3600, show_spinner="Loading 2 years of trading volume…")
def get_volumes(tickers: tuple) -> pd.DataFrame:
    return load_volumes(list(tickers))


def analyze(w: pd.Series):
    """Run the full AUREN engine on one portfolio. Returns None if data is too short."""
    active_w = w[w > 0]
    if active_w.empty:
        return None
    prices = get_prices(tuple(sorted(active_w.index))).dropna()
    if len(prices) < 30:
        return None
    c = concentration(active_w)
    pr = portfolio_returns(prices, active_w)
    vol, mdd = volatility(pr), max_drawdown(pr)
    value = (1 + pr).cumprod()
    drawdown = value / value.cummax() - 1
    corr = correlation(prices, active_w.index)
    pairs = high_pairs(corr)
    exposure = sector_exposure(active_w)
    periods = worst_periods(pr)
    max_sector_val = float(exposure.max()) if not exposure.empty else 0.0
    score, level, hits = risk_score(c, vol, mdd, pairs, max_sector_val)

    return dict(prices=prices, c=c, pr=pr, vol=vol, mdd=mdd, value=value,
                drawdown=drawdown, corr=corr, pairs=pairs, exposure=exposure,
                score=score, level=level, hits=hits, periods=periods)


PF_COLUMNS = {
    "ticker": st.column_config.SelectboxColumn(
        "Ticker", options=sorted(SECTORS), required=True),
    "weight": st.column_config.NumberColumn(
        "Weight %", min_value=0.0, max_value=100.0, step=1.0, format="%.1f"),
}

PRESETS = {
    "Custom / Edited": None,
    "Balanced Tech & Crypto (Default)": [
        {"ticker": "NVDA", "weight": 40.0},
        {"ticker": "MSFT", "weight": 30.0},
        {"ticker": "GOOGL", "weight": 20.0},
        {"ticker": "ETH-USD", "weight": 10.0},
    ],
    "Magnificent 7 Tech Heavy": [
        {"ticker": "NVDA", "weight": 25.0},
        {"ticker": "MSFT", "weight": 20.0},
        {"ticker": "AAPL", "weight": 20.0},
        {"ticker": "AMZN", "weight": 15.0},
        {"ticker": "GOOGL", "weight": 10.0},
        {"ticker": "META", "weight": 10.0},
    ],
    "Diversified All-Weather": [
        {"ticker": "MSFT", "weight": 20.0},
        {"ticker": "JPM", "weight": 20.0},
        {"ticker": "COST", "weight": 20.0},
        {"ticker": "GLD", "weight": 20.0},
        {"ticker": "BTC-USD", "weight": 10.0},
        {"ticker": "ETH-USD", "weight": 10.0},
    ],
    "High Conviction Semiconductor": [
        {"ticker": "NVDA", "weight": 50.0},
        {"ticker": "TSM", "weight": 25.0},
        {"ticker": "ASML", "weight": 15.0},
        {"ticker": "AMD", "weight": 10.0},
    ],
}

# ---------------------------------------------------------- session state
DEFAULT_PF = pd.DataFrame(PRESETS["Balanced Tech & Crypto (Default)"])
st.session_state.setdefault("pf_df", DEFAULT_PF)
st.session_state.setdefault("pf_v", 0)
st.session_state.setdefault("size", 10000.0)
st.session_state.setdefault("wallet_msg", None)
st.session_state.setdefault("wallet_info", None)


def load_wallet():
    """Button callback: read a public Base address and fill the portfolio."""
    addr = st.session_state.get("wallet_addr", "").strip()
    st.session_state.wallet_info = None
    if not is_valid_address(addr):
        st.session_state.wallet_msg = (
            "error", "Enter a valid Base address: 0x followed by 40 hex characters.")
        return
    try:
        info = wallet_holdings(addr, set(SECTORS),
                               setting("BASE_RPC_URL", BASE_RPC))
    except Exception as e:
        st.session_state.wallet_msg = (
            "error", f"Could not read the wallet right now ({type(e).__name__}). "
                     "Try again in a minute.")
        return
    st.session_state.wallet_info = info
    df, total, skipped = holdings_to_portfolio(info["rows"])
    if df.empty:
        st.session_state.wallet_msg = (
            "warning", "No supported tokenized stocks found in this wallet.")
        return
    st.session_state.pf_df = df.reset_index(drop=True)
    st.session_state.pf_v += 1
    st.session_state.size = max(100.0, round(total, 2))
    extra = f" {len(skipped)} other holding(s) skipped." if skipped else ""
    st.session_state.wallet_msg = (
        "success", f"Loaded {len(df)} supported holding(s), about ${total:,.0f}.{extra}")


# ------------------------------------------------------------------- hero
st.markdown('<div class="wordmark"><span class="ring">◐</span>AUREN</div>'
            '<div class="tagline">See the risk before it sees you. Deterministic risk intelligence.</div>',
            unsafe_allow_html=True)

# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown('<div class="wordmark small"><span class="ring">◐</span>AUREN</div>',
                unsafe_allow_html=True)

    # Preset selector
    selected_preset = st.selectbox(
        "Portfolio Presets",
        options=list(PRESETS.keys()),
        index=1,
        help="Quickly load pre-configured realistic portfolios."
    )
    if selected_preset != "Custom / Edited" and PRESETS[selected_preset] is not None:
        preset_df = pd.DataFrame(PRESETS[selected_preset])
        # Only overwrite if current df differs from selected preset
        if not st.session_state.pf_df.equals(preset_df):
            st.session_state.pf_df = preset_df
            st.session_state.pf_v += 1
            st.rerun()

    st.markdown("##### Your portfolio")
    pf = st.data_editor(
        st.session_state.pf_df, num_rows="dynamic", hide_index=True,
        key=f"pf_{st.session_state.pf_v}", column_config=PF_COLUMNS)
    pf = pf.dropna(subset=["ticker", "weight"])
    total = float(pf["weight"].sum())
    ok = abs(total - 100) <= 0.01

    t_col1, t_col2 = st.columns([1, 1])
    with t_col1:
        st.markdown(f'<span class="chip {"ok" if ok else "bad"}">Total: {total:.1f}%</span>',
                    unsafe_allow_html=True)
    with t_col2:
        if not ok and total > 0:
            if st.button("Normalize to 100%", help="Rescales weights to sum to 100% proportionally"):
                pf["weight"] = (pf["weight"] / total * 100).round(1)
                st.session_state.pf_df = pf.reset_index(drop=True)
                st.session_state.pf_v += 1
                st.rerun()

    st.number_input("Portfolio size ($)", min_value=100.0, step=500.0, key="size")
    st.caption("Weights must add up to 100%.")

    with st.expander("Base wallet (read-only)"):
        st.text_input("Public address", key="wallet_addr", placeholder="0x…")
        st.button("Load tokenized stocks", on_click=load_wallet)
        msg = st.session_state.wallet_msg
        if msg:
            {"error": st.error, "warning": st.warning,
             "success": st.success}[msg[0]](msg[1])
        st.caption("Read-only: AUREN only reads public token balances. "
                   "Never paste a private key or seed phrase. "
                   "Addresses are never stored.")
    st.caption("Analytics only, not investment advice.")

# ------------------------------------------------------------- validation
if pf.empty:
    st.info("Add at least one holding in the sidebar to begin.")
    st.stop()
if pf["ticker"].duplicated().any():
    dup_tickers = ", ".join(pf[pf["ticker"].duplicated()]["ticker"].unique())
    st.error(f"Duplicate holding found: {dup_tickers}. Each ticker can appear only once.")
    st.stop()
if not ok:
    st.error(f"Weights add up to {total:.1f}%. They need to add up to 100%. Use 'Normalize to 100%' in the sidebar if needed.")
    st.stop()

weights = pd.Series(pf["weight"].values / 100, index=pf["ticker"].values)
n = len(weights)
size = float(st.session_state.size)

A = analyze(weights)
if A is None:
    st.error("Not enough historical price data for these tickers. Try other holdings.")
    st.stop()

prices, c, pr, vol, mdd = A["prices"], A["c"], A["pr"], A["vol"], A["mdd"]
value, drawdown, corr, pairs = A["value"], A["drawdown"], A["corr"], A["pairs"]
exposure, score, level, hits = A["exposure"], A["score"], A["level"], A["hits"]
periods = A["periods"]

# Live score card in sidebar
badge_cls = "badge-low" if level == "Low" else "badge-med" if level == "Medium" else "badge-high"
with st.sidebar:
    st.markdown(
        '<div class="card" style="text-align:center;margin-top:14px">'
        '<div class="label">Risk score</div>'
        f'<div class="value gold" style="font-size:2.4rem">{score}'
        '<span style="font-size:0.9rem;color:#8A8F98"> / 100</span></div>'
        f'<div class="sub"><span class="{badge_cls}">{level} Risk</span></div></div>',
        unsafe_allow_html=True)

# ------------------------------------------------------------------- tabs
tab_pf, tab_conc, tab_score, tab_risk, tab_stress, tab_liq, tab_corr, tab_whatif, tab_ai = st.tabs([
    "Portfolio",
    "Concentration",
    "Risk Overview",
    "Historical Risk",
    "Stress Tests",
    "Liquidity",
    "Correlation",
    "What-if",
    "AI Report"
])

# ================================================================ 1. Portfolio
with tab_pf:
    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(card("Portfolio value", f"${size:,.0f}", "Size set in the sidebar"),
                unsafe_allow_html=True)
    k2.markdown(card("Largest holding",
                      f"{c['top_asset']} · {c['top_weight']:.0%}",
                      "Single-asset weight"), unsafe_allow_html=True)
    k3.markdown(card("Effective assets", f"{c['effective_assets']:.1f}",
                      f"Behaves like {c['effective_assets']:.1f} equal holdings, not {n}",
                      gold=True), unsafe_allow_html=True)
    k4.markdown(card("Top sector", f"{exposure.max():.0%}", exposure.idxmax()),
                unsafe_allow_html=True)

    left, right = st.columns([1.1, 1])
    with left:
        section("Holdings", "Each asset, its industry, and dollar value")
        holdings = pd.DataFrame({
            "Ticker": weights.index,
            "Industry": [SECTORS.get(t, "Unknown") for t in weights.index],
            "Sector Group": [GROUPS.get(t, "Other") for t in weights.index],
            "Weight %": weights.values * 100,
            "Value ($)": weights.values * size,
        })
        st.dataframe(
            holdings, hide_index=True,
            column_config={
                "Weight %": st.column_config.ProgressColumn(
                    "Weight %", min_value=0, max_value=100, format="%.1f%%"),
                "Value ($)": st.column_config.NumberColumn("Value ($)", format="$%,.0f"),
            })
    with right:
        section("Allocation", "Share of the portfolio by holding")
        donut_colors = [GOLD if t == c["top_asset"] else ASSET_GREYS[i % len(ASSET_GREYS)]
                        for i, t in enumerate(weights.index)]
        fig = go.Figure(go.Pie(
            labels=list(weights.index), values=list(weights.values), hole=0.62,
            sort=False, marker=dict(colors=donut_colors, line=dict(color=BG, width=2)),
            textinfo="label+percent", textposition="outside",
            textfont=dict(color=TEXT),
            hovertemplate="%{label}: %{percent} ($%{value:,.0f})<extra></extra>",
            customdata=list(weights.values * size)))
        fig.add_annotation(text=f"${size:,.0f}", showarrow=False,
                           font=dict(size=18, color=TEXT, family="JetBrains Mono"))
        style(fig, height=320)
        fig.update_layout(showlegend=False)
        with st.container(border=True):
            st.plotly_chart(fig)

    section("Broad sector exposure (Risk Groups)",
            "Groups correlated industries together to catch hidden cluster risks")
    ex = exposure.sort_values()
    colors = [GOLD if s == exposure.idxmax() else "#5B5F68" for s in ex.index]
    fig = go.Figure(go.Bar(
        x=ex.values, y=ex.index, orientation="h", marker_color=colors,
        text=[f"{v:.1%}" for v in ex.values], textposition="outside",
        textfont=dict(color=TEXT), hovertemplate="%{y}: %{x:.1%}<extra></extra>"))
    fig.add_vline(x=0.50, line_dash="dash", line_color=DANGER,
                  annotation_text="50% sector rule (+15 pts)", annotation_font_color=DANGER)
    style(fig, height=max(220, 55 * len(ex) + 60))
    fig.update_xaxes(tickformat=".0%", range=[0, max(0.55, min(1.0, float(ex.max()) * 1.25))])
    fig.update_yaxes(gridcolor="rgba(0,0,0,0)")
    with st.container(border=True):
        st.plotly_chart(fig)

    info = st.session_state.wallet_info
    if info and info["rows"]:
        with st.expander("Tokenized stocks detected in the Base wallet"):
            det = pd.DataFrame([{
                "Token": r["token"], "Underlying": r["ticker"],
                "Tokens": r["tokens"], "Shares": r["shares"],
                "Price ($)": r["price"], "Value ($)": r["value"],
                "Analysed": "Yes" if r["supported"] and r["value"] > 0 else "No",
            } for r in info["rows"]])
            st.dataframe(det, hide_index=True)
            st.caption("Value = token balance × Chainlink reference price. Shares apply "
                       "the token's multiplier. Reference prices can be stale outside "
                       "market hours. Only holdings marked Yes are analysed.")
    elif info is not None:
        st.caption(f"Wallet read successful ({info['n_tokens']} tokenized stocks checked), "
                   "but none are held at this address.")

# ============================================================== 2. Concentration
with tab_conc:
    cc1, cc2, cc3, cc4 = st.columns(4)
    cc1.markdown(card("Largest holding",
                      f"{c['top_asset']} · {c['top_weight']:.0%}",
                      "Over 30% triggers +20 risk pts"), unsafe_allow_html=True)
    cc2.markdown(card("Top 3 holdings", f"{c['top3_weight']:.0%}",
                      "Share held in the 3 largest positions"),
                 unsafe_allow_html=True)
    cc3.markdown(card("Effective assets", f"{c['effective_assets']:.1f}",
                      f"Inverse HHI: behaves like {c['effective_assets']:.1f} equal assets", gold=True),
                 unsafe_allow_html=True)
    cc4.markdown(card("Concentration index", f"{c['hhi']:.2f}",
                      "HHI: 1.00 = all in 1 asset; 0.10 = well diversified"),
                 unsafe_allow_html=True)

    section("Holdings by weight", "The dashed line is AUREN's 30% single-holding rule")
    wts = weights.sort_values()
    bar_colors = [GOLD if v > 0.30 else "#5B5F68" for v in wts.values]
    fig = go.Figure(go.Bar(
        x=wts.values, y=wts.index, orientation="h", marker_color=bar_colors,
        text=[f"{v:.1%}" for v in wts.values], textposition="outside",
        textfont=dict(color=TEXT), hovertemplate="%{y}: %{x:.1%}<extra></extra>"))
    fig.add_vline(x=0.30, line_dash="dash", line_color=GREY,
                  annotation_text="30% threshold", annotation_font_color=GREY)
    style(fig, height=max(240, 55 * len(wts) + 60))
    fig.update_xaxes(tickformat=".0%",
                     range=[0, max(0.35, min(1.0, float(wts.max()) * 1.25))])
    fig.update_yaxes(gridcolor="rgba(0,0,0,0)")
    with st.container(border=True):
        st.plotly_chart(fig)

    if c["top_weight"] > 0.30:
        st.markdown(callout(
            f"<b>Concentration Warning:</b> <b>{c['top_asset']}</b> represents {c['top_weight']:.1%} of the portfolio, "
            f"exceeding the 30% threshold. Severe single-asset dependence (+20 risk pts).", danger=True),
            unsafe_allow_html=True)
    else:
        st.markdown(callout(
            f"<b>Well-Distributed:</b> No single holding exceeds 30%. The largest holding, <b>{c['top_asset']}</b>, "
            f"is {c['top_weight']:.1%}.", muted=True), unsafe_allow_html=True)

    drop = 0.20
    st.markdown(callout(
        f"<b>Illustrative Shock:</b> If {c['top_asset']} dropped {drop:.0%}, the portfolio would "
        f"lose approximately <b>{c['top_weight'] * drop:.1%} (${c['top_weight'] * drop * size:,.0f})</b> from that holding alone. "
        f"Arithmetic illustration, not a market forecast.", muted=True),
        unsafe_allow_html=True)

    with st.expander("Mathematical derivation (HHI & Effective Assets)"):
        terms = " + ".join(f"{w:.2f}²" for w in weights.sort_values(ascending=False))
        st.markdown(
            f"**Herfindahl-Hirschman Index (HHI):**\n"
            f"$$\\text{{HHI}} = \\sum w_i^2 = {terms} = \\mathbf{{{c['hhi']:.4f}}}$$\n\n"
            f"**Effective Number of Assets ($N_{{\\text{{eff}}}}$):**\n"
            f"$$N_{{\\text{{eff}}}} = \\frac{{1}}{{\\text{{HHI}}}} = \\frac{{1}}{{{c['hhi']:.4f}}} = \\mathbf{{{c['effective_assets']:.2f}}}$$\n\n"
            f"If all {n} holdings were equally weighted at {100/n:.1f}%, $N_{{\\text{{eff}}}}$ would equal **{n:.1f}**.")
    st.caption("Concentration reflects current weights, independent of historical prices. Analytics only.")

# ============================================================== 3. Risk Overview
with tab_score:
    left, right = st.columns([1, 1.6])
    with left:
        st.markdown(
            '<div class="card" style="text-align:center">'
            '<div class="label">Total Risk score</div>'
            f'<div class="value gold" style="font-size:4.2rem">{score}'
            '<span style="font-size:1.3rem;color:#8A8F98"> / 100</span></div>'
            f'<div class="sub">Risk Tier: <span class="{badge_cls}">{level}</span></div>'
            '</div>', unsafe_allow_html=True)
        st.progress(score / 100)
        st.caption("Calculated purely from deterministic risk thresholds.")
    with right:
        section("Audited rule breakdown", "Every score point is accounted for with an auditable rule")
        if hits:
            for pts, why in hits:
                st.markdown(callout(f"<b>+{pts} pts</b> · {why}"), unsafe_allow_html=True)
        else:
            st.markdown(callout("✓ Clean sheet: No risk rules triggered for this portfolio.", muted=True),
                        unsafe_allow_html=True)

    with st.expander("View complete AUREN rulebook (6 Audited Rules)"):
        rule_df = pd.DataFrame(RULE_TABLE, columns=["Points", "Rule"])
        st.dataframe(rule_df, hide_index=True)
        st.caption("AUREN rules are open and audited. Zero black-box parameters.")
    st.caption("A rule-based measure of past data, not a prediction. Analytics only, not investment advice.")

# ============================================================== 4. Historical Risk
with tab_risk:
    r1, r2, r3, r4 = st.columns(4)
    r1.markdown(card("Volatility (annual)", f"{vol:.1%}",
                     "Annualised daily standard deviation", gold=True),
                unsafe_allow_html=True)
    r2.markdown(card("Worst drawdown", f"{mdd:.1%}",
                     f"Trough occurred {drawdown.idxmin():%d %b %Y}",
                     color="danger" if mdd < -0.30 else ""),
                unsafe_allow_html=True)
    r3.markdown(card("Worst single day", f"{periods['worst_day']:.1%}",
                     "Biggest single session drop"),
                unsafe_allow_html=True)
    r4.markdown(card("Worst 21-day month", f"{periods['worst_month']:.1%}",
                     "Worst rolling 21 trading days"),
                unsafe_allow_html=True)

    section("Rebased price history", "All assets rebased to 100 at start of lookback. Gold line represents your portfolio.")
    norm = prices / prices.iloc[0] * 100
    fig = go.Figure()
    for i, col in enumerate(norm.columns):
        fig.add_trace(go.Scatter(
            x=norm.index, y=norm[col], name=col, mode="lines",
            line=dict(width=1.2, color=ASSET_GREYS[i % len(ASSET_GREYS)])))
    fig.add_trace(go.Scatter(
        x=value.index, y=value.values * 100, name="Portfolio (Gold)", mode="lines",
        line=dict(width=3, color=GOLD)))
    style(fig, height=380)
    fig.update_layout(yaxis_title="Index (Base = 100)")
    with st.container(border=True):
        st.plotly_chart(fig)

    section("Drawdown profile (Underwater chart)", "Distance from historical peak over time")
    trough = drawdown.idxmin()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=drawdown.index, y=drawdown.values, mode="lines", name="Drawdown",
        line=dict(color=GOLD, width=2), fill="tozeroy",
        fillcolor="rgba(227,179,65,0.15)",
        hovertemplate="%{x|%d %b %Y}: %{y:.1%}<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=[trough], y=[mdd], mode="markers+text", showlegend=False,
        text=[f"Trough: {mdd:.1%}"], textposition="bottom center",
        textfont=dict(color=DANGER, size=13), marker=dict(color=DANGER, size=10)))
    style(fig, height=330)
    fig.update_yaxes(tickformat=".0%", range=[mdd * 1.35, 0.02])
    with st.container(border=True):
        st.plotly_chart(fig)
    st.caption("Based on 2 years of daily close data. Past performance does not predict future returns.")

# ============================================================== 5. Stress Tests (NEW)
with tab_stress:
    section("Scenario stress testing",
            "Simulate severe historical and hypothetical market dislocations on your exact holdings.")

    st_cols = st.columns(4)
    scen_results = []
    for idx, (scen_name, scen_shocks) in enumerate(SCENARIOS.items()):
        impact = stress(weights, scen_shocks)
        dollar_impact = impact * size
        scen_results.append({
            "Scenario": scen_name,
            "Impact %": impact,
            "Estimated Loss ($)": dollar_impact,
            "Portfolio Value After ($)": size * (1 + impact)
        })
        col = st_cols[idx % 4]
        col.markdown(card(
            scen_name,
            f"{impact:+.1%}",
            f"{dollar_impact:+,.0f} USD impact",
            color="danger" if impact < -0.15 else "gold"
        ), unsafe_allow_html=True)

    section("Preset shock comparison")
    scen_df = pd.DataFrame(scen_results)
    st.dataframe(
        scen_df, hide_index=True,
        column_config={
            "Impact %": st.column_config.ProgressColumn(
                "Impact %", min_value=-0.50, max_value=0.10, format="%+.1f%%"),
            "Estimated Loss ($)": st.column_config.NumberColumn(
                "Estimated Loss ($)", format="$%,.0f"),
            "Portfolio Value After ($)": st.column_config.NumberColumn(
                "Portfolio Value After ($)", format="$%,.0f")
        })

    section("Custom sector shock simulator",
            "Adjust expected shock per sector group to evaluate portfolio resilience")
    present_groups = sorted(set(GROUPS.get(t, "Other") for t in weights.index))
    custom_shocks = {}
    slider_cols = st.columns(min(4, max(1, len(present_groups))))
    for i, g in enumerate(present_groups):
        with slider_cols[i % len(slider_cols)]:
            custom_shocks[g] = st.slider(f"{g} shock", min_value=-50, max_value=20, value=0, step=5, format="%d%%") / 100.0

    custom_impact = stress(weights, custom_shocks)
    custom_dollar = custom_impact * size
    res_col1, res_col2 = st.columns([1, 2])
    with res_col1:
        st.markdown(card(
            "Custom shock result",
            f"{custom_impact:+.1%}",
            f"{custom_dollar:+,.0f} USD on ${size:,.0f} portfolio",
            color="danger" if custom_impact < 0 else "success" if custom_impact > 0 else ""
        ), unsafe_allow_html=True)
    with res_col2:
        if custom_impact < 0:
            st.markdown(callout(
                f"Under this custom shock, your portfolio declines by <b>{custom_impact:.1%}</b> "
                f"(a drop of <b>${abs(custom_dollar):,.0f}</b>).", danger=True), unsafe_allow_html=True)
        elif custom_impact > 0:
            st.markdown(callout(
                f"Under this custom shock, your portfolio gains <b>{custom_impact:+.1%}</b> "
                f"(a rise of <b>${custom_dollar:,.0f}</b>)."), unsafe_allow_html=True)
        else:
            st.markdown(callout("Move the sliders to see hypothetical stress test impact.", muted=True), unsafe_allow_html=True)

    st.caption("Stress tests assume static portfolio weights and instantaneous sector shocks. Not investment advice.")

# ============================================================== 6. Liquidity (NEW)
with tab_liq:
    section("Liquidity analysis (Days to Exit)",
            "Measures how many trading days are needed to exit each holding assuming a conservative 10% daily volume participation rate.")

    volumes = get_volumes(tuple(sorted(weights.index)))
    adv = avg_daily_value(prices, volumes, window=30)
    pos_values = weights * size
    dte = days_to_exit(pos_values, adv, participation=0.10)

    lq1, lq2, lq3 = st.columns(3)
    max_dte_ticker = dte.idxmax() if not dte.empty else "N/A"
    max_dte_val = dte.max() if not dte.empty else 0.0
    lq1.markdown(card("Max days to exit", f"{max_dte_val:.2f} days", f"Holding: {max_dte_ticker}"), unsafe_allow_html=True)
    lq2.markdown(card("Participation rate", "10%", "Standard conservative liquidation cap"), unsafe_allow_html=True)
    lq3.markdown(card("30D average volume", "Active", "Computed over last 30 trading sessions", gold=True), unsafe_allow_html=True)

    liq_rows = []
    for t in weights.index:
        v_daily = adv.get(t, float("nan"))
        days = dte.get(t, float("nan"))
        pos_val = pos_values[t]
        liq_rows.append({
            "Ticker": t,
            "Position ($)": pos_val,
            "30D Daily Traded ($)": v_daily,
            "10% Cap ($/day)": v_daily * 0.10 if pd.notna(v_daily) else float("nan"),
            "Days to Exit": days,
            "Liquidity Status": "Instant (<0.1d)" if days < 0.1 else "Liquid (<1d)" if days < 1.0 else "Illiquid (1d+)"
        })
    liq_df = pd.DataFrame(liq_rows)

    st.dataframe(
        liq_df, hide_index=True,
        column_config={
            "Position ($)": st.column_config.NumberColumn("Position ($)", format="$%,.0f"),
            "30D Daily Traded ($)": st.column_config.NumberColumn("30D Daily Traded ($)", format="$%,.0f"),
            "10% Cap ($/day)": st.column_config.NumberColumn("10% Cap ($/day)", format="$%,.0f"),
            "Days to Exit": st.column_config.NumberColumn("Days to Exit", format="%.3f"),
        }
    )

    if max_dte_val > 1.0:
        st.markdown(callout(
            f"<b>Liquidity Notice:</b> Liquidating <b>{max_dte_ticker}</b> would require more than 1 full trading day "
            f"({max_dte_val:.2f} days) at 10% volume participation.", danger=True), unsafe_allow_html=True)
    else:
        st.markdown(callout("✓ All portfolio positions can be fully liquidated in under 1 trading day at 10% volume participation.", muted=True), unsafe_allow_html=True)

    st.caption("Volume data from Yahoo Finance. Crypto volumes are USD-denominated. Past trading volume may dry up during crises.")

# ============================================================== 7. Correlation
with tab_corr:
    cols = list(corr.columns)
    all_pairs = [(a, b, float(corr.loc[a, b]))
                 for i, a in enumerate(cols) for b in cols[i + 1:]]
    top = max(all_pairs, key=lambda p: p[2]) if all_pairs else None

    q1, q2 = st.columns(2)
    if top:
        q1.markdown(card("Most correlated pair", f"{top[0]} · {top[1]}",
                         f"Correlation {top[2]:.2f}"), unsafe_allow_html=True)
    else:
        q1.markdown(card("Most correlated pair", "–",
                         "Add at least 2 holdings to evaluate"), unsafe_allow_html=True)
    q2.markdown(card("Pairs above 0.7", f"{len(pairs)}",
                     f"Out of {len(all_pairs)} pairs total", gold=True),
                unsafe_allow_html=True)

    section("Correlation heatmap",
            "Brighter gold indicates pairs moving together in tandem ($r > 0.70$)")
    fig = px.imshow(corr, text_auto=".2f", zmin=-1, zmax=1, aspect="auto",
                    color_continuous_scale=["#18181B", GOLD])
    fig.update_coloraxes(showscale=False)
    fig.update_traces(textfont=dict(size=14))
    style(fig, height=420)
    fig.update_xaxes(gridcolor="rgba(0,0,0,0)")
    fig.update_yaxes(gridcolor="rgba(0,0,0,0)")
    with st.container(border=True):
        st.plotly_chart(fig)

    if pairs:
        for a, b, v in pairs:
            st.markdown(callout(f"<b>{a}</b> and <b>{b}</b> exhibit high correlation (r = {v:.2f}). "
                                f"They offer limited diversification benefits and may drop together."), unsafe_allow_html=True)
    else:
        st.markdown(callout("✓ Low co-movement: No pair exceeds the 0.70 correlation threshold in this portfolio.",
                            muted=True), unsafe_allow_html=True)
    st.caption("Based on 2-year daily percentage returns. Past correlations are non-stationary.")

# ============================================================== 8. What-if
with tab_whatif:
    section("What-if scenario comparison",
            "Modify the second portfolio below to compare risk side-by-side with your current portfolio.")
    sig = str(abs(hash(tuple(zip(weights.index, weights.round(4))))))
    base_b = pd.DataFrame({"ticker": list(weights.index),
                           "weight": list(weights.values * 100)})
    wb_df = st.data_editor(base_b, num_rows="dynamic", hide_index=True,
                           key=f"pfb_{sig}", column_config=PF_COLUMNS)
    wb_df = wb_df.dropna(subset=["ticker", "weight"])
    tot_b = float(wb_df["weight"].sum())
    ok_b = abs(tot_b - 100) <= 0.01

    wb_col1, wb_col2 = st.columns([1, 1])
    with wb_col1:
        st.markdown(f'<span class="chip {"ok" if ok_b else "bad"}">What-if total: {tot_b:.1f}%</span>', unsafe_allow_html=True)
    with wb_col2:
        if not ok_b and tot_b > 0:
            if st.button("Normalize What-if to 100%"):
                wb_df["weight"] = (wb_df["weight"] / tot_b * 100).round(1)
                st.session_state[f"pfb_{sig}"] = wb_df.reset_index(drop=True)
                st.rerun()

    if wb_df.empty or wb_df["ticker"].duplicated().any():
        st.info("Add holdings with no duplicate tickers to compare.")
    elif not ok_b:
        st.warning("What-if weights must add up to 100%.")
    else:
        wb = pd.Series(wb_df["weight"].values / 100, index=wb_df["ticker"].values)
        B = analyze(wb)
        if B is None:
            st.error("Not enough price history for the what-if tickers.")
        else:
            d = B["score"] - A["score"]
            note = ("Lower risk score (-%d pts)" % abs(d) if d < 0 else
                    "Higher risk score (+%d pts)" % d if d > 0 else "No change")
            w1, w2, w3 = st.columns(3)
            w1.markdown(card("Current score", f"{A['score']}", A["level"]),
                        unsafe_allow_html=True)
            w2.markdown(card("What-if score", f"{B['score']}", B["level"], gold=True),
                        unsafe_allow_html=True)
            w3.markdown(card("Delta", f"{d:+d}", note, color="success" if d < 0 else "danger" if d > 0 else ""), unsafe_allow_html=True)

            section("Side-by-side metric comparison")
            rows = [
                ("Risk score", f"{A['score']} ({A['level']})", f"{B['score']} ({B['level']})"),
                ("Largest holding", f"{A['c']['top_asset']} · {A['c']['top_weight']:.1%}",
                 f"{B['c']['top_asset']} · {B['c']['top_weight']:.1%}"),
                ("Top 3 holdings", f"{A['c']['top3_weight']:.1%}",
                 f"{B['c']['top3_weight']:.1%}"),
                ("Effective number of assets", f"{A['c']['effective_assets']:.1f}",
                 f"{B['c']['effective_assets']:.1f}"),
                ("Top sector group", f"{A['exposure'].idxmax()} · {A['exposure'].max():.1%}",
                 f"{B['exposure'].idxmax()} · {B['exposure'].max():.1%}"),
                ("Volatility (annual)", f"{A['vol']:.1%}", f"{B['vol']:.1%}"),
                ("Worst drawdown", f"{A['mdd']:.1%}", f"{B['mdd']:.1%}"),
                ("Correlated pairs (>0.7)", str(len(A["pairs"])), str(len(B["pairs"]))),
            ]
            st.dataframe(pd.DataFrame(rows, columns=["Metric", "Current", "What-if"]),
                         hide_index=True)

            rc1, rc2 = st.columns(2)
            with rc1:
                st.markdown("**Current: Triggered Rules**")
                for pts, why in A["hits"]:
                    st.markdown(callout(f"<b>+{pts}</b> · {why}", muted=True),
                                unsafe_allow_html=True)
                if not A["hits"]:
                    st.caption("No rules triggered.")
            with rc2:
                st.markdown("**What-if: Triggered Rules**")
                for pts, why in B["hits"]:
                    st.markdown(callout(f"<b>+{pts}</b> · {why}"),
                                unsafe_allow_html=True)
                if not B["hits"]:
                    st.caption("No rules triggered.")

            section("Historical drawdown: Current vs What-if",
                    "Simulated past drawdown profile with identical lookback window")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=A["drawdown"].index, y=A["drawdown"].values,
                                     name="Current", line=dict(color="#7A7F88", width=2)))
            fig.add_trace(go.Scatter(x=B["drawdown"].index, y=B["drawdown"].values,
                                     name="What-if", line=dict(color=GOLD, width=2.5)))
            style(fig, height=320)
            fig.update_yaxes(tickformat=".0%")
            with st.container(border=True):
                st.plotly_chart(fig)
    st.caption("Comparative analysis of historical backtest data. Analytics only.")

# ============================================================== 9. AI Report
with tab_ai:
    section("Deterministic AI risk report",
            "Audited synthesis: The engine computes the mathematical ground truth; the LLM articulates clear qualitative explanations.")

    stress_dict = {name: stress(weights, s) for name, s in SCENARIOS.items()}
    metrics = {
        "risk_score": score,
        "risk_level": level,
        "score_reasons": [why for _, why in hits],
        "portfolio_value_usd": round(size, 2),
        "holdings_weight": {t: round(float(w), 4) for t, w in weights.items()},
        "largest_holding": {c["top_asset"]: round(c["top_weight"], 4)},
        "top_3_holdings_weight": round(c["top3_weight"], 4),
        "concentration_index_hhi": round(c["hhi"], 4),
        "effective_assets": round(c["effective_assets"], 2),
        "volatility_annualised": round(vol, 4),
        "max_drawdown": round(mdd, 4),
        "worst_day": round(periods["worst_day"], 4),
        "worst_month": round(periods["worst_month"], 4),
        "sector_exposure": {k: round(float(v), 4) for k, v in exposure.items()},
        "correlated_pairs_above_0.7": [[a, b, v] for a, b, v in pairs],
        "scenario_stress_shocks": {k: round(v, 4) for k, v in stress_dict.items()},
    }
    metrics_json = json.dumps(metrics, sort_keys=True, default=str)

    base_url = setting("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    model = setting("LLM_MODEL", "openai/gpt-oss-120b")
    api_key = setting("LLM_API_KEY", "")
    local = "localhost" in (base_url or "") or "127.0.0.1" in (base_url or "")
    configured = bool(base_url and model and (api_key or local))

    if not configured:
        api_key = st.text_input(
            "Groq / OpenAI API Key", type="password",
            help="Configured via .env or entered here for this session.")
        configured = bool(base_url and model and api_key)
        if not configured:
            st.info("Enter your LLM API Key to generate an AI Risk Report.")

    rep = st.session_state.get("report")
    if st.button("Generate AI Report", disabled=not configured):
        try:
            with st.spinner("Generating grounded risk intelligence report…"):
                text = ai_report(metrics, base_url, api_key, model)
            st.session_state.report = (metrics_json, text)
            rep = st.session_state.report
        except Exception as e:
            st.error(f"Could not generate report: {e}")

    if rep:
        if rep[0] != metrics_json:
            st.markdown(callout("The portfolio configuration has changed since this report was generated. Click 'Generate AI Report' to refresh.", muted=True), unsafe_allow_html=True)
        st.markdown(rep[1])
        bad = unverified_numbers(rep[1], metrics)
        if bad:
            st.warning("Hallucination guard: These figures appeared in the report without matching deterministic engine metrics: "
                       + ", ".join(f"{b:g}" for b in bad)
                       + ". Verify them against the engine data below.")
        else:
            st.caption("✓ Hallucination check passed: All numerical citations in the report match deterministic engine output.")

        reasons = [f"- +{p} · {why}" for p, why in hits] or ["- No rules triggered"]
        md = "\n".join([
            "# AUREN Risk Intelligence Report", "",
            f"**Risk Score:** {score} / 100 ({level} Risk)", "",
            "## Score Breakdown", *reasons, "",
            "## Key Financial Metrics",
            f"- Largest Holding: {c['top_asset']} ({c['top_weight']:.1%})",
            f"- Top 3 Holdings: {c['top3_weight']:.1%}",
            f"- Effective Assets (1/HHI): {c['effective_assets']:.1f}",
            f"- Annualised Volatility: {vol:.1%}",
            f"- Maximum Drawdown: {mdd:.1%}", "",
            "## AI Risk Assessment", rep[1], "",
            "_Analytics only, not investment advice. Past performance is no guarantee of future returns._"])
        st.download_button("Download Report (.md)", md, "auren-risk-report.md", mime="text/markdown")

    with st.expander("Inspect Deterministic Metrics JSON (Ground Truth)"):
        st.json(metrics)

# ----------------------------------------------------------------- footer
st.markdown('<div class="footer"><b>AUREN Deterministic Risk Engine</b> · Analytics only, not investment advice. '
            'Past performance does not predict future results. Price and volume data sourced via Yahoo Finance '
            '(unofficial, demo analytics). Base on-chain tokenized balances resolved via Base RPC.</div>',
            unsafe_allow_html=True)
