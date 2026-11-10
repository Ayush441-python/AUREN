import streamlit as st
import pandas as pd
from engine.universe import SECTORS

st.set_page_config(page_title="AUREN", layout="wide")
st.title("AUREN")
st.caption("Financial risk intelligence · Analytics only, not investment advice")

st.subheader("Your portfolio")
default = pd.DataFrame({"ticker": ["NVDA", "MSFT", "GOOGL", "ETH-USD"],
                        "weight": [40, 30, 20, 10]})
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