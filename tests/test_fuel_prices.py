
from pathlib import Path
import pandas as pd

RAW_DIR = Path("data/raw")

files = list(RAW_DIR.glob("fuel_prices.parquet"))

if not files:
    raise FileNotFoundError("No Parquet files found.")

latest_file = max(files, key=lambda f: f.stat().st_mtime)

df = pd.read_parquet(latest_file)

print("File:", latest_file.name)
print("Total rows:", len(df))
print("Total columns:", len(df.columns))

print("\nSeries types:")
print(df["series_type"].value_counts(dropna=False))

print("\nMissing values:")
print(df.isnull().sum())

print("\nDate range:")
print(df["date"].min(), "to", df["date"].max())

print("\nSample data:")
print(df.head(10))
