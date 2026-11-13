import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from engine.data import load_prices
from engine.metrics import (concentration, portfolio_returns, volatility,
                            max_drawdown, correlation, high_pairs)
from engine.universe import SECTORS

st.set_page_config(page_title="AUREN · See the risk before it sees you",
                   layout="wide")

# ------------------------------------------------------------------ brand
GOLD, GREY, PANEL, BG = "#E3B341", "#8A8F98", "#18181B", "#0E0E10"
TEXT, GRID = "#F5F6F7", "#26262B"
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
.block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1180px; }
section[data-testid="stSidebar"] { background: #121215; border-right: 1px solid #26262B; }

.wordmark { font-weight: 700; letter-spacing: 0.38em; font-size: 2.1rem;
            color: #F5F6F7; line-height: 1; }
.wordmark .ring { color: #E3B341; margin-right: 0.55rem; letter-spacing: 0; }
.wordmark.small { font-size: 1.1rem; margin-bottom: 1.2rem; }
.tagline { color: #8A8F98; margin-top: 0.7rem; font-size: 1.02rem; }

.section-title { font-size: 1.05rem; font-weight: 600; color: #F5F6F7;
                 margin: 1.6rem 0 0.2rem 0; }
.section-sub { color: #8A8F98; font-size: 0.88rem; margin-bottom: 0.7rem; }

.card { background: #18181B; border: 1px solid #26262B; border-radius: 14px;
        padding: 18px 20px; height: 100%; }
.card .label { color: #8A8F98; font-size: 0.74rem; text-transform: uppercase;
               letter-spacing: 0.09em; font-weight: 600; }
.card .value { font-family: 'JetBrains Mono', monospace; font-weight: 700;
               font-size: 2rem; color: #F5F6F7; margin: 6px 0 4px 0; }
.card .value.gold { color: #E3B341; }
.card .sub { color: #8A8F98; font-size: 0.82rem; line-height: 1.35; }

.callout { border-left: 3px solid #E3B341; background: #18181B;
           border-radius: 8px; padding: 12px 16px; margin: 8px 0;
           color: #F5F6F7; font-size: 0.95rem; }
.callout.muted { border-left-color: #44474F; color: #8A8F98; }

.chip { display: inline-block; padding: 4px 12px; border-radius: 999px;
        font-size: 0.8rem; font-weight: 600;
        font-family: 'JetBrains Mono', monospace; }
.chip.ok { background: rgba(227,179,65,0.14); color: #E3B341; }
.chip.bad { background: rgba(245,246,247,0.08); color: #F5F6F7; }

.footer { color: #8A8F98; font-size: 0.8rem; margin-top: 2.5rem;
          padding-top: 1rem; border-top: 1px solid #26262B; }

button[data-baseweb="tab"] { font-weight: 600; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------- helpers
def card(label, value, sub="", gold=False):
    cls = "value gold" if gold else "value"
    return (f'<div class="card"><div class="label">{label}</div>'
            f'<div class="{cls}">{value}</div><div class="sub">{sub}</div></div>')


def callout(text, muted=False):
    cls = "callout muted" if muted else "callout"
    return f'<div class="{cls}">{text}</div>'


def section(title, sub=""):
    st.markdown(f'<div class="section-title">{title}</div>'
                f'<div class="section-sub">{sub}</div>', unsafe_allow_html=True)


def style(fig, height=380, title=None):
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


# ------------------------------------------------------------------- hero
st.markdown('<div class="wordmark"><span class="ring">◐</span>AUREN</div>'
            '<div class="tagline">See the risk before it sees you.</div>',
            unsafe_allow_html=True)

# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown('<div class="wordmark small"><span class="ring">◐</span>AUREN</div>',
                unsafe_allow_html=True)
    st.markdown("##### Your portfolio")

    default = pd.DataFrame({"ticker": ["NVDA", "MSFT", "GOOGL", "ETH-USD"],
                            "weight": [40.0, 30.0, 20.0, 10.0]})
    pf = st.data_editor(
        default, num_rows="dynamic", hide_index=True, key="pf",
        column_config={
            "ticker": st.column_config.SelectboxColumn(
                "Ticker", options=sorted(SECTORS), required=True),
            "weight": st.column_config.NumberColumn(
                "Weight %", min_value=0.0, max_value=100.0, step=1.0,
                format="%.1f"),
        },
    )
    pf = pf.dropna(subset=["ticker", "weight"])
    total = float(pf["weight"].sum())
    ok = abs(total - 100) <= 0.01
    st.markdown(f'<span class="chip {"ok" if ok else "bad"}">Total: {total:.1f}%</span>',
                unsafe_allow_html=True)
    st.caption("Weights must add up to 100%. Add or remove rows with the table controls.")
    st.caption("Analytics only, not investment advice.")

# ------------------------------------------------------------- validation
if pf.empty:
    st.info("Add at least one holding in the sidebar to begin.")
    st.stop()
if pf["ticker"].duplicated().any():
    st.error("Each ticker can appear only once. Merge the duplicate rows in the sidebar.")
    st.stop()
if not ok:
    st.error(f"Weights add up to {total:.1f}%. They need to add up to 100%.")
    st.stop()

weights = pd.Series(pf["weight"].values / 100, index=pf["ticker"].values)
n = len(weights)

prices = get_prices(tuple(sorted(weights.index))).dropna()
if len(prices) < 30:
    st.error("Not enough price history for these tickers. Try other holdings.")
    st.stop()

# ----------------------------------------------------------- calculations
c = concentration(weights)
pr = portfolio_returns(prices, weights)
vol = volatility(pr)
mdd = max_drawdown(pr)
value = (1 + pr).cumprod()
drawdown = value / value.cummax() - 1
corr = correlation(prices, weights.index)
pairs = high_pairs(corr)
exposure = weights.groupby(lambda t: SECTORS[t]).sum().sort_values(ascending=False)

# ------------------------------------------------------------------- tabs
tab_pf, tab_risk, tab_corr = st.tabs(["Portfolio", "Risk", "Correlation"])

# ---- Portfolio
with tab_pf:
    k1, k2, k3 = st.columns(3)
    k1.markdown(card("Largest holding",
                     f"{c['top_asset']} · {c['top_weight']:.0%}",
                     "How much rides on one holding"), unsafe_allow_html=True)
    k2.markdown(card("Effective number of assets", f"{c['effective_assets']:.1f}",
                     f"Behaves like {c['effective_assets']:.1f} equal-sized "
                     f"holdings, not {n}", gold=True), unsafe_allow_html=True)
    k3.markdown(card("Top sector", f"{exposure.max():.0%}", exposure.idxmax()),
                unsafe_allow_html=True)

    left, right = st.columns([1, 1.15])
    with left:
        section("Holdings", "Each asset and the sector it belongs to")
        holdings = pd.DataFrame({
            "Ticker": weights.index,
            "Sector": [SECTORS[t] for t in weights.index],
            "Weight %": weights.values * 100,
        })
        st.dataframe(
            holdings, hide_index=True,
            column_config={"Weight %": st.column_config.ProgressColumn(
                "Weight %", min_value=0, max_value=100, format="%.1f")},
        )
    with right:
        section("Sector exposure", "Where the portfolio is really invested")
        ex = exposure.sort_values()
        colors = [GOLD if s == exposure.idxmax() else "#5B5F68" for s in ex.index]
        fig = go.Figure(go.Bar(
            x=ex.values, y=ex.index, orientation="h", marker_color=colors,
            text=[f"{v:.0%}" for v in ex.values], textposition="outside",
            textfont=dict(color=TEXT), hovertemplate="%{y}: %{x:.1%}<extra></extra>"))
        style(fig, height=max(220, 60 * len(ex) + 60))
        fig.update_xaxes(tickformat=".0%", range=[0, min(1.0, ex.max() * 1.2)])
        fig.update_yaxes(gridcolor="rgba(0,0,0,0)")
        with st.container(border=True):
            st.plotly_chart(fig)

# ---- Risk
with tab_risk:
    r1, r2, r3 = st.columns(3)
    r1.markdown(card("Volatility (annualised)", f"{vol:.1%}",
                     "How much the value swings in a typical year", gold=True),
                unsafe_allow_html=True)
    r2.markdown(card("Worst drawdown", f"{mdd:.1%}",
                     f"Peak-to-bottom fall, trough on "
                     f"{drawdown.idxmin():%d %b %Y}"), unsafe_allow_html=True)
    r3.markdown(card("Days analysed", f"{len(pr)}",
                     "Trading days where every asset has a price"),
                unsafe_allow_html=True)

    section("Price history", "Every asset rebased to 100. Gold is your portfolio.")
    norm = prices / prices.iloc[0] * 100
    fig = go.Figure()
    for i, col in enumerate(norm.columns):
        fig.add_trace(go.Scatter(
            x=norm.index, y=norm[col], name=col, mode="lines",
            line=dict(width=1.3, color=ASSET_GREYS[i % len(ASSET_GREYS)])))
    fig.add_trace(go.Scatter(
        x=value.index, y=value.values * 100, name="Portfolio", mode="lines",
        line=dict(width=3, color=GOLD)))
    style(fig, height=380)
    with st.container(border=True):
        st.plotly_chart(fig)

    section("Drawdown",
            "How far the portfolio sat below its previous peak")
    trough = drawdown.idxmin()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=drawdown.index, y=drawdown.values, mode="lines", name="Drawdown",
        line=dict(color=GOLD, width=2), fill="tozeroy",
        fillcolor="rgba(227,179,65,0.15)",
        hovertemplate="%{x|%d %b %Y}: %{y:.1%}<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=[trough], y=[mdd], mode="markers+text", showlegend=False,
        text=[f"{mdd:.1%}"], textposition="bottom center",
        textfont=dict(color=GOLD, size=13),
        marker=dict(color=GOLD, size=9)))
    style(fig, height=330)
    fig.update_yaxes(tickformat=".0%", range=[mdd * 1.3, 0.02])
    with st.container(border=True):
        st.plotly_chart(fig)
    st.caption("Based on past data. Past data does not predict the future. "
               "Analytics only, not investment advice.")

# ---- Correlation
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
                         "Add a second holding to compare"), unsafe_allow_html=True)
    q2.markdown(card("Pairs above 0.7", f"{len(pairs)}",
                     f"Out of {len(all_pairs)} pairs", gold=True),
                unsafe_allow_html=True)

    section("Correlation heatmap",
            "Brighter gold means the assets tend to move together")
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
            st.markdown(callout(f"<b>{a}</b> and <b>{b}</b> move together ({v}). "
                                f"They may fall together."), unsafe_allow_html=True)
    else:
        st.markdown(callout("No pair is above 0.7 correlation in this portfolio.",
                            muted=True), unsafe_allow_html=True)
    st.caption("Based on past data. Past data does not predict the future. "
               "Analytics only, not investment advice.")

# ----------------------------------------------------------------- footer
st.markdown('<div class="footer">Analytics only, not investment advice. '
            'Past data does not predict the future. Price data from Yahoo '
            'Finance via yfinance (unofficial, for demo analytics only).</div>',
            unsafe_allow_html=True)