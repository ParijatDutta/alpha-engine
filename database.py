import pandas as pd
import os

DATA_PATH = "sp500_metadata.parquet"

def initialize_sp500():
    """Pulls S&P 500 metadata from Wikipedia and saves locally."""
    if not os.path.exists(DATA_PATH):
        # One-time pull of tickers and sectors
        table = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
        df = table[['Symbol', 'Security', 'GICS Sector', 'GICS Sub-Industry']]
        df.to_parquet(DATA_PATH)
        return df
    return pd.read_parquet(DATA_PATH)

def load_metadata():
    return pd.read_parquet(DATA_PATH)