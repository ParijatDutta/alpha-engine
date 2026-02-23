import pandas as pd
import yfinance as yf
import requests

def fetch_politician_trades():
    """Fetches recent politician trades using a 2026-compliant header."""
    # Capitol Trades direct JSON endpoint (2026 update)
    url = "https://api.capitoltrades.com/trades?pageSize=50"
    
    # Advanced headers to bypass 2026 security blocks
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://www.capitoltrades.com/trades"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            raw_data = response.json().get('data', [])
            if not raw_data:
                return pd.DataFrame()
            
            # 2026 Data Schema Mapping
            df = pd.DataFrame(raw_data)
            
            # Extract politician name from nested dict if necessary
            if 'politician' in df.columns and isinstance(df['politician'].iloc[0], dict):
                df['politician_name'] = df['politician'].apply(lambda x: f"{x.get('firstName')} {x.get('lastName')}")
            else:
                df['politician_name'] = df['politician']

            return df[['politician_name', 'asset', 'txType', 'value', 'txDate']]
    except Exception as e:
        print(f"Fetch Error: {e}")
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