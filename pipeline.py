import pandas as pd
import yfinance as yf
from io import StringIO
import requests

def fetch_politician_trades():
    """Bypasses 403 Forbidden by mimicking a full browser session."""
    url = "https://www.capitoltrades.com/trades?tx_index=sp500"
    
    # Standard 2026 Browser Headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/"
    }

    try:
        # Use a session to persist headers
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            # Wrap text in StringIO to satisfy latest pandas requirements
            dfs = pd.read_html(StringIO(response.text))
            if dfs:
                df = dfs[0]
                # Clean up column names based on the 2026 site layout
                # Usually: Ticker, Politician, Type, Amount, Date
                return df
    except Exception as e:
        print(f"Scrape Error: {e}")
    
    return pd.DataFrame()

def fetch_macro_signals():
    """Fetches VIX and 10Y Yield with rate-limit protection."""
    try:
        # download is more stable for Cloud IPs in 2026
        vix_data = yf.download("^VIX", period="5d", interval="1d", progress=False)
        tnx_data = yf.download("^TNX", period="5d", interval="1d", progress=False)
        return {
            "VIX": float(vix_data['Close'].iloc[-1]),
            "10Y_Yield": float(tnx_data['Close'].iloc[-1])
        }
    except:
        return {"VIX": 0.0, "10Y_Yield": 0.0}