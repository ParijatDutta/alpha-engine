import requests
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf

def fetch_politician_trades():
    """Fetches recent politician trades from Capitol Trades JSON API."""
    url = "https://api.capitoltrades.com/trades?pageSize=50"
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code == 200:
            data = response.json()['data']
            df = pd.DataFrame(data)
            # Filter for S&P 500 relevant info (Ticker and Type)
            return df[['asset', 'politician', 'txDate', 'txType', 'value']]
    except Exception as e:
        print(f"Politician Trade Error: {e}")
    return pd.DataFrame()

def fetch_macro_signals():
    """Fetches key macro data: 10Y Yield and Inflation proxy."""
    # Using public data proxies to avoid needing private API keys for now
    signals = {
        "10Y_Yield": yf.Ticker("^TNX").history(period="1d")['Close'].iloc[-1],
        "VIX": yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
    }
    return signals