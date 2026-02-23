import yfinance as yf
import pandas as pd
import requests

def fetch_macro_signals():
    """Fetches VIX and 10Y Yield with rate-limit protection."""
    try:
        # download is generally more robust than Ticker.history for cloud IPs
        vix_data = yf.download("^VIX", period="5d", interval="1d", progress=False)
        tnx_data = yf.download("^TNX", period="5d", interval="1d", progress=False)
        
        # Get the last valid closing price
        vix = vix_data['Close'].iloc[-1]
        tnx = tnx_data['Close'].iloc[-1]
        
        # Handle cases where yfinance returns a Series instead of a float
        return {
            "VIX": float(vix), 
            "10Y_Yield": float(tnx)
        }
    except Exception as e:
        print(f"Macro Fetch Error: {e}")
        return {"VIX": 0.0, "10Y_Yield": 0.0}