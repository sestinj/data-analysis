import yfinance as yf
import pandas as pd

df = yf.Ticker("MSFT").history(period="max")
print(df)