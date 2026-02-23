import pandas as pd
import requests
from io import StringIO

def scrape_and_save():
    url = "https://www.capitoltrades.com/trades?tx_index=sp500"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        df = pd.read_html(StringIO(response.text))[0]
        df.to_csv("daily_trades.csv", index=False)
        print("Successfully saved trades.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    scrape_and_save()