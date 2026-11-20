from engine.data import load_prices, load_volumes
from engine.universe import SECTORS

tickers = list(SECTORS)
load_prices(tickers).to_csv("data/prices.csv")
load_volumes(tickers).to_csv("data/volume.csv")
print("Saved data/prices.csv and data/volume.csv")