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
    """Fetches key Buffett-style metrics for a list of tickers."""
    # To keep your Chromebook/Streamlit memory safe, we fetch in small batches
    enriched_results = []
    
    # We use yf.download for price and Ticker.info for fundamentals
    # Note: In a free tier, we limit this to a subset for the first run
    for t in tickers[:20]: # Start with 20 to test stability
        try:
            tk = yf.Ticker(t)
            info = tk.info
            enriched_results.append({
                "Symbol": t,
                "Price": info.get("currentPrice"),
                "EPS": info.get("trailingEps"),
                "BVPS": info.get("bookValue"),
                "ROE": info.get("returnOnEquity"),
                "MarketCap": info.get("marketCap")
            })
        except:
            continue
            
    return pd.DataFrame(enriched_results)