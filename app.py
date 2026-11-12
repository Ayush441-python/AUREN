import streamlit as st
import pandas as pd
from engine.universe import SECTORS
from engine.metrics import concentration, portfolio_returns, volatility, max_drawdown


st.set_page_config(page_title="AUREN", layout="wide")
st.title("AUREN")
st.caption("Financial risk intelligence · Analytics only, not investment advice")

st.subheader("Your portfolio")
default = pd.DataFrame({"ticker": ["NVDA", "MSFT", "GOOGL", "ETH-USD"],
                        "weight": [50, 10, 30, 10]})
pf = st.data_editor(default, num_rows="dynamic", key="pf")

total = pf["weight"].sum()
if abs(total - 100) > 0.01:
    st.error(f"Weights add up to {total}%. They need to add up to 100%.")
    st.stop()

unknown = [t for t in pf["ticker"] if t not in SECTORS]
if unknown:
    st.warning(f"Not in AUREN's list yet: {', '.join(unknown)}")
    st.stop()

weights = pd.Series(pf["weight"].values / 100, index=pf["ticker"])

st.subheader("Sectors")
sector_view = pd.DataFrame({
    "ticker": weights.index,
    "weight %": (weights.values * 100).round(1),
    "sector": [SECTORS[t] for t in weights.index],
})
st.dataframe(sector_view, hide_index=True)


from engine.metrics import concentration

st.subheader("Concentration")
c = concentration(weights)
col1, col2 = st.columns(2)
col1.metric("Largest holding", f"{c['top_asset']} · {c['top_weight']:.0%}")
col2.metric("Effective number of assets", f"{c['effective_assets']:.1f}")


from engine.data import load_prices


@st.cache_data(ttl=3600)
def get_prices(tickers: tuple) -> pd.DataFrame:
    return load_prices(list(tickers))


prices = get_prices(tuple(weights.index)).dropna()

st.subheader("Price history")
st.caption(f"{len(prices)} trading days · "
           f"{prices.index.min().date()} to {prices.index.max().date()}")
st.line_chart(prices / prices.iloc[0] * 100)


import plotly.express as px

st.subheader("Volatility and drawdown")
pr = portfolio_returns(prices, weights)
vol = volatility(pr)
mdd = max_drawdown(pr)

col3, col4 = st.columns(2)
col3.metric("Volatility (annualised)", f"{vol:.1%}")
col4.metric("Worst drawdown (past 2 years)", f"{mdd:.1%}")

value = (1 + pr).cumprod()
drawdown = value / value.cummax() - 1
fig = px.line(x=drawdown.index, y=drawdown.values)
fig.update_traces(line_color="#E3B341")
fig.update_layout(
    title="Drawdown: how far the portfolio sat below its previous peak",
    xaxis_title=None,
    yaxis_title=None,
    yaxis_tickformat=".0%",
    showlegend=False,
)
st.plotly_chart(fig, use_container_width=True)
st.caption("Based on past data. Past data does not predict the future. "
           "Analytics only, not investment advice.")