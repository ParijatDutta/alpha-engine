import pandas as pd
import yfinance as yf
import os
import requests
from io import StringIO

DATA_PATH = "sp500_fundamentals.parquet"

def initialize_sp500():
    """Initializes the base S&P 500 list from Wikipedia."""
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    df = pd.read_html(StringIO(response.text))[0]
    df = df[['Symbol', 'Security', 'GICS Sector']]
    return df

def get_enriched_data(tickers):
    enriched_results = []
    for t in tickers[:30]:
        try:
            tk = yf.Ticker(t)
            info = tk.info
            
            # Key Buffett/Graham Metrics
            enriched_results.append({
                "Symbol": t,
                "Price": info.get("currentPrice") or info.get("previousClose"),
                "EPS": info.get("trailingEps", 0),
                "BVPS": info.get("bookValue", 0),
                "ROE": info.get("returnOnEquity", 0),
                "DivYield": info.get("dividendYield", 0),
                # Analyst 5-year growth estimate (crucial for DCF)
                "GrowthRate": info.get("earningsGrowth", 0.05) # Default 5% if missing
            })
        except Exception: continue
    return pd.DataFrame(enriched_results)