
import os

from dotenv import load_dotenv
from google.cloud import bigquery


load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
LOCATION = os.getenv("GCP_LOCATION", "asia-southeast1")


def get_bigquery_client():

    if not PROJECT_ID:
        raise ValueError(
            "GCP_PROJECT_ID is missing from .env"
        )

    client = bigquery.Client(
        project=PROJECT_ID,
        location=LOCATION
    )

    return client


if __name__ == "__main__":

    client = get_bigquery_client()

    print("BigQuery connection successful!")
    print("Project:", client.project)
    print("Location:", LOCATION)
