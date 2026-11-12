from engine.data import load_prices
from engine.universe import SECTORS

load_prices(list(SECTORS)).to_csv("data/prices.csv")
print("Saved data/prices.csv")