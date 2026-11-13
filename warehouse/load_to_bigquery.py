
import re
import tempfile
from pathlib import Path

import pandas as pd
from google.cloud import bigquery

from warehouse.bigquery_client import (
    get_bigquery_client,
    PROJECT_ID
)


RAW_DIR = Path("data/raw")

DATASETS = {
    "fuel_prices.parquet": "fuel_prices",
    "crude_oil.parquet": "crude_oil",
    "exchange_rates.parquet": "exchange_rates"
}


def clean_column_names(df):

    new_columns = []
    used_names = set()

    for column in df.columns:

        name = str(column).lower()
        name = re.sub(r"[^a-z0-9_]", "_", name)
        name = re.sub(r"_+", "_", name).strip("_")

        if not name:
            name = "column"

        if name[0].isdigit():
            name = f"col_{name}"

        base_name = name
        counter = 1

        while name in used_names:
            name = f"{base_name}_{counter}"
            counter += 1

        used_names.add(name)
        new_columns.append(name)

    df.columns = new_columns

    return df


def load_parquet_to_bigquery(
    client,
    file_name,
    table_name
):

    source_file = RAW_DIR / file_name

    if not source_file.exists():
        raise FileNotFoundError(
            f"File not found: {source_file}"
        )

    print(f"\nLoading: {source_file}")

    df = pd.read_parquet(source_file)

    if df.empty:
        raise ValueError(
            f"{file_name} contains no records."
        )

    df = clean_column_names(df)

    with tempfile.TemporaryDirectory() as temp_dir:

        temp_file = Path(temp_dir) / file_name

        df.to_parquet(
            temp_file,
            engine="pyarrow",
            index=False
        )

        table_id = (
            f"{PROJECT_ID}.raw.{table_name}"
        )

        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.PARQUET,
            autodetect=True,
            write_disposition=(
                bigquery.WriteDisposition.WRITE_TRUNCATE
            )
        )

        with open(temp_file, "rb") as file:

            load_job = client.load_table_from_file(
                file,
                table_id,
                job_config=job_config
            )

        load_job.result()

    table = client.get_table(table_id)

    print(f"Loaded successfully: {table_id}")
    print(f"Rows loaded: {table.num_rows}")
    print(f"Columns: {len(table.schema)}")


def main():

    client = get_bigquery_client()

    for file_name, table_name in DATASETS.items():

        load_parquet_to_bigquery(
            client,
            file_name,
            table_name
        )


if __name__ == "__main__":
    main()
