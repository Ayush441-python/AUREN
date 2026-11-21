from engine.data import load_prices, load_unadjusted_prices, load_volumes
from engine.universe import SECTORS

tickers = list(SECTORS)
load_prices(tickers).to_csv("data/prices.csv")
load_unadjusted_prices(tickers).to_csv("data/raw_prices.csv")
load_volumes(tickers).to_csv("data/volume.csv")
print("Saved data/prices.csv, data/raw_prices.csv, and data/volume.csv")