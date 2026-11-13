
from pathlib import Path

from warehouse.bigquery_client import get_bigquery_client


SQL_DIR = Path("sql")


def execute_sql_file(file_path):

    client = get_bigquery_client()

    if not file_path.exists():
        raise FileNotFoundError(file_path)

    query = file_path.read_text(encoding="utf-8")

    print(f"Executing: {file_path}")

    query_job = client.query(query)

    query_job.result()

    print("SQL executed successfully!")
    print("Job ID:", query_job.job_id)


def main():

    sql_files = [
        SQL_DIR / "staging" / "stg_fuel_prices.sql",
        SQL_DIR / "staging" / "stg_exchange_rates.sql",
        SQL_DIR / "staging" / "stg_crude_oil.sql",
        SQL_DIR / "marts" / "fact_fuel_prices.sql",
        SQL_DIR / "marts" / "fact_exchange_rates.sql",
        SQL_DIR / "marts" / "fact_crude_oil.sql"
    ]

    for sql_file in sql_files:
        execute_sql_file(sql_file)


if __name__ == "__main__":
    main()
