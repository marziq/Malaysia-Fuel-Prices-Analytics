
import requests
import pandas as pd
import fastparquet as pq
import pyarrow as pa  
from pathlib import Path

API_URL = (
    "https://api.data.gov.my/data-catalogue?id=fuelprice&limit=3"
)

PARAMS = {
    "id": "fuelprice",
    "filter": "level@series_type",
    "sort": "-date",
    "limit": 10000
}

def extract_fuel_prices():

    response = requests.get(
        API_URL,
        params=PARAMS,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    df = pd.DataFrame(data)

    return df


def main():

    df = extract_fuel_prices()

    print("API extraction successful!")
    print(df.head())
    print(df.info())

    # Create raw data directory
    RAW_DIR = Path("data/raw")
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # Save extracted data
    output_file = RAW_DIR / "fuel_prices.parquet"

    df.to_parquet(
        output_file,
        engine="fastparquet",
        index=False
    )


if __name__ == "__main__":
    main()
