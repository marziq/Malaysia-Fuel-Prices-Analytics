
from google.cloud import bigquery

from warehouse.bigquery_client import (
    get_bigquery_client,
    PROJECT_ID,
    LOCATION
)


DATASETS = [
    "raw",
    "staging",
    "mart"
]


def create_datasets():

    client = get_bigquery_client()

    for dataset_name in DATASETS:

        dataset_id = f"{PROJECT_ID}.{dataset_name}"

        dataset = bigquery.Dataset(dataset_id)
        dataset.location = LOCATION

        client.create_dataset(
            dataset,
            exists_ok=True
        )

        print(f"Dataset ready: {dataset_id}")


def main():

    create_datasets()


if __name__ == "__main__":
    main()
