
import requests
import pandas as pd
import fastparquet as pq
import pyarrow as pa  
from pathlib import Path

API_URL = (
    "https://api.bnm.gov.my/public/exchange-rate/USD?session=0900&quote=rm"
)


import requests
import pandas as pd


def extract_exchange_rates():

    url = "https://api.bnm.gov.my/public/exchange-rate"

    headers = {
        "Accept": "application/vnd.BNM.API.v1+json"
    }

    params = {
        "session": "0900",
        "quote": "rm"
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30
    )

    # Check API response
    response.raise_for_status()

    # Convert JSON response
    data = response.json()

    # Convert API records into DataFrame
    df = pd.json_normalize(data["data"])

    # Keep USD records only
    if "currency_code" in df.columns:
        df = df[df["currency_code"] == "USD"]

    print("BNM exchange rate extraction successful!")
    print(df.head())
    print(df.info())

    return df



def main():

    df = extract_exchange_rates()

    print("API extraction successful!")
    print(df.head())
    print(df.info())

    # Create raw data directory
    RAW_DIR = Path("data/raw")
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # Save extracted data
    output_file = RAW_DIR / "exchange_rates.parquet"

    df.to_parquet(
        output_file,
        engine="fastparquet",
        index=False
    )


if __name__ == "__main__":
    main()
