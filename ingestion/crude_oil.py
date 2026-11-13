
import os
import requests
import pandas as pd
import fastparquet as pq
import pyarrow as pa
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv("EIA_API_KEY")

API_URL = (
    "https://api.eia.gov/v2/petroleum/pri/spt/data/"
)

PARAMS = {
    "api_key": API_KEY,
    "frequency": "daily",
    "data[0]": "value",
    "facets[series][]": "RWTC",
    "sort[0][column]": "period",
    "sort[0][direction]": "desc",
    "offset": 0,
    "length": 5000
}


def extract_crude_oil_prices():

    all_data = []
    offset = 0

    while True:

        params = PARAMS.copy()
        params["offset"] = offset

        response = requests.get(
            API_URL,
            params=params,
            timeout=30
        )

        # Display API error details if request fails
        if not response.ok:
            print("API Error:", response.status_code)
            print(response.text)
            response.raise_for_status()

        data = response.json()

        records = data["response"]["data"]

        if not records:
            break

        all_data.extend(records)

        print(
            f"Extracted {len(records)} records. "
            f"Total: {len(all_data)}"
        )

        if len(records) < PARAMS["length"]:
            break

        offset += PARAMS["length"]

    df = pd.DataFrame(all_data)

    return df


def main():

    if not API_KEY:
        raise ValueError(
            "EIA_API_KEY not found. Check your .env file."
        )

    df = extract_crude_oil_prices()

    print("EIA API extraction successful!")
    print(df.head())
    print(df.info())

    # Create raw data directory
    RAW_DIR = Path("data/raw")
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # Save extracted data
    output_file = RAW_DIR / "crude_oil.parquet"

    df.to_parquet(
        output_file,
        engine="fastparquet",
        index=False
    )

    print(f"Data saved successfully: {output_file}")


if __name__ == "__main__":
    main()
