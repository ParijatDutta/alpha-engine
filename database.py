import pandas as pd
import os
import requests
from io import StringIO

DATA_PATH = "sp500_metadata.parquet"

def initialize_sp500():
    if not os.path.exists(DATA_PATH):
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        # Pretend to be a browser to avoid 403 Forbidden
        headers = {"User-Agent": "Mozilla/5.0"}
        
        response = requests.get(url, headers=headers)
        # Use StringIO to avoid future pandas warnings
        df = pd.read_html(StringIO(response.text))[0]
        
        df = df[['Symbol', 'Security', 'GICS Sector', 'GICS Sub-Industry']]
        df.to_parquet(DATA_PATH)
        return df
    return pd.read_parquet(DATA_PATH)

def load_metadata():
    return pd.read_parquet(DATA_PATH)