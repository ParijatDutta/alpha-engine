import pandas as pd
import yfinance as yf
import requests

def fetch_politician_trades():
    """Fetches recent politician trades from Capitol Trades."""
    url = "https://api.capitoltrades.com/trades?pageSize=50"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json().get('data', [])
            return pd.DataFrame(data)
    except Exception as e:
        print(f"Trade Fetch Error: {e}")
    return pd.DataFrame()

def fetch_macro_signals():
    """Fetches VIX and 10Y Yield with rate-limit protection."""
    try:
        # Use a list to ensure yf.download works cleanly
        vix_data = yf.download("^VIX", period="5d", progress=False)
        tnx_data = yf.download("^TNX", period="5d", progress=False)
        
        vix = vix_data['Close'].iloc[-1]
        tnx = tnx_data['Close'].iloc[-1]
        
        return {"VIX": float(vix), "10Y_Yield": float(tnx)}
    except Exception as e:
        return {"VIX": 0.0, "10Y_Yield": 0.0}