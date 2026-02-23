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
            # Fetching 1y history for Moving Averages
            hist = tk.history(period="1y")
            
            # Technicals
            current_price = info.get("currentPrice") or info.get("previousClose")
            ma_50 = hist['Close'].tail(50).mean()
            ma_200 = hist['Close'].tail(200).mean()
            
            enriched_results.append({
                "Symbol": t,
                "Price": current_price,
                "EPS": info.get("trailingEps", 0),
                "GrowthRate": info.get("earningsGrowth", 0.15), # 2026 avg is ~15%
                "ROE": info.get("returnOnEquity", 0),
                "DivYield": info.get("dividendYield", 0),
                "52W_High": info.get("fiftyTwoWeekHigh"),
                "52W_Low": info.get("fiftyTwoWeekLow"),
                "Trend": "🚀 Bullish" if ma_50 > ma_200 else "⚠️ Bearish",
                "Distance_from_Low": (current_price - info.get("fiftyTwoWeekLow")) / info.get("fiftyTwoWeekLow") if info.get("fiftyTwoWeekLow") else 0
            })
        except: continue
    return pd.DataFrame(enriched_results)