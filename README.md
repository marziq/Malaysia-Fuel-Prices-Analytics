# Malaysia Fuel Prices Analytics

A Python and BigQuery pipeline for collecting Malaysian retail fuel prices, USD/MYR exchange rates, and the EIA's WTI crude oil price series. The pipeline saves source data as Parquet, validates the files, and can optionally load them into BigQuery and build staging and mart tables.

> **Pipeline status:** ingestion, Parquet validation, BigQuery dataset/table loading, and SQL transformations are runnable as separate commands. Run them manually in the order below. `dags/energy_pipeline_dag.py` is currently empty; there is no configured Airflow scheduler or automatic orchestration.

## What the pipeline does

1. Retrieves fuel prices from the [Malaysia Data Catalogue API](https://api.data.gov.my/).
2. Retrieves USD/MYR exchange rates from the [Bank Negara Malaysia API](https://api.bnm.gov.my/).
3. Retrieves the WTI crude oil spot price series (`RWTC`) from the [U.S. Energy Information Administration API](https://www.eia.gov/opendata/).
4. Writes the source data to Parquet files under `data/raw/`.
5. Checks file schemas, required columns, values, duplicates, dates, and data freshness. Writes a CSV report and a log.
6. Optionally creates BigQuery datasets, loads the Parquet files into raw tables, and executes the staging and mart SQL.

## Project layout

| Path | Purpose |
| --- | --- |
| `ingestion/` | One extraction script for each data source |
| `validation/validate_parquet.py` | Parquet schema and data-quality checks |
| `data/raw/` | Extracted Parquet files and the validation report |
| `warehouse/` | BigQuery client, dataset creation, loading, and SQL execution |
| `sql/staging/` | SQL that casts and cleans the raw source tables |
| `sql/marts/` | SQL that builds analytical fact tables |
| `tests/test_fuel_prices.py` | Script for inspecting the fuel price Parquet file |
| `dags/energy_pipeline_dag.py` | Reserved for orchestration; currently empty |
| `requirements.txt` | Python package dependencies |

Generated files:

- `data/raw/fuel_prices.parquet`
- `data/raw/exchange_rates.parquet`
- `data/raw/crude_oil.parquet`
- `data/raw/validation_report.csv`
- `logs/validation.log`

## Run it from your own VS Code

### 1. Install the prerequisites

Install:

- [Git](https://git-scm.com/downloads)
- [Visual Studio Code](https://code.visualstudio.com/)
- A supported Python installation
- The VS Code **Python** extension (Microsoft)

The BigQuery portion additionally needs a Google Cloud project with the BigQuery API enabled and permission to create datasets/tables and run query jobs.

### 2. Get the project and open it

If the project is published in a Git repository, copy its clone URL and use either approach:

**VS Code**

1. Open VS Code.
2. Open **Source Control** and select **Clone Repository**, or open the Command Palette and run **Git: Clone**.
3. Paste the repository URL, choose a local destination, and open the cloned folder.
4. If prompted, trust the folder and install/recommend the Python extension.

**Terminal**

Replace `<repository-url>` with the URL for this project:

```powershell
git clone <repository-url>
cd <cloned-folder>
code .
```

If you received the project as a ZIP instead, extract it, then use **File > Open Folder** in VS Code to open the extracted project root (the folder containing `requirements.txt`).

### 3. Create and select a Python environment

Open VS Code's integrated terminal (**Terminal > New Terminal**) at the project root.

In PowerShell, create and activate a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt instead:

```bat
py -m venv .venv
.\.venv\Scripts\activate.bat
```

In VS Code, open the Command Palette, run **Python: Select Interpreter**, and select the interpreter inside `.venv`. Then install the project dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Run subsequent commands from the project root with this environment active. The modules use project-relative paths such as `data/raw` and `sql`.

### 4. Configure the EIA API key

If you do not already have a `.env` file, copy the example in the project root. Use the command for your terminal:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

In Git Bash:

```bash
test -e .env || cp .env.example .env
```

Then edit `.env` and replace `replace_with_your_eia_api_key` with your EIA API key. If `.env` already exists, edit it instead of replacing it. Only the crude oil extraction requires an API key. The fuel price and exchange rate scripts use public APIs. Keep your real `.env` private; it is ignored by Git.

### 5. Extract the source data

Run each extractor from the project root:

```powershell
python -m ingestion.fuel_prices
python -m ingestion.exchange_rates
python -m ingestion.crude_oil
```

Each command writes its Parquet file to `data/raw/`, creating the directory if needed. Re-running an extractor replaces that source file with the latest response; these scripts do not maintain a historical archive.

### 6. Validate the Parquet files

```powershell
python -m validation.validate_parquet
```

The command reports validation results in the terminal, writes `data/raw/validation_report.csv`, and appends details to `logs/validation.log`. A validation failure raises an error and should be investigated before loading the data.

The configured freshness limits are 14 days for fuel prices and 7 days for exchange rates and crude oil. A source outage, an old API response, or a changed source schema can therefore cause validation to fail.

## Optional: load and transform data in BigQuery

The local extraction and validation steps do not require Google Cloud. To use BigQuery, configure credentials and project access first.

### 1. Configure Google Cloud

Create or select a Google Cloud project, enable the BigQuery API, and authenticate with an identity that can create datasets, load data, and run BigQuery jobs. For local development, the Google Cloud CLI's Application Default Credentials are one option:

```powershell
gcloud auth application-default login
```

In `.env`, replace `your-gcp-project-id` with your Google Cloud project ID. The example uses `asia-southeast1` for `GCP_LOCATION`; change it if your BigQuery datasets use another location.

**Important:** the SQL files currently refer directly to the BigQuery project `malaysia-fuel-analytics`. Set `GCP_PROJECT_ID` to that project to use the SQL unchanged. If you use another project, update the project IDs in the SQL files under `sql/` as well. `GCP_LOCATION` defaults to `asia-southeast1`; use a location compatible with your project and datasets.

Do not store service-account credentials in the repository. If your environment requires a service-account key, keep it outside the project and configure the Google authentication environment according to your organization's security policy.

### 2. Create datasets

```powershell
python -m warehouse.create_datasets
```

This creates (or reuses) the `raw`, `staging`, and `mart` datasets in the configured project and location.

### 3. Load the raw tables

```powershell
python -m warehouse.load_to_bigquery
```

This loads the three Parquet files into:

- `raw.fuel_prices`
- `raw.exchange_rates`
- `raw.crude_oil`

The load jobs autodetect the schema and use `WRITE_TRUNCATE`, so a new run **replaces** the corresponding raw table contents. Ensure the files exist and have passed validation before running this step.

### 4. Build staging and mart tables

```powershell
python -m warehouse.run_sql
```

The script runs the staging SQL first, followed by the mart SQL. It creates or replaces:

- `staging.stg_fuel_prices`
- `staging.stg_exchange_rates`
- `staging.stg_crude_oil`
- `mart.fact_fuel_prices`
- `mart.fact_exchange_rates`
- `mart.fact_crude_oil`

The fuel price mart SQL also runs a monthly summary query after creating its fact table. Review the SQL files before running them in a shared or production project; the table statements replace existing tables with the same names.

## Inspect the extracted fuel prices

After extracting fuel prices, run the included inspection script:

```powershell
python tests/test_fuel_prices.py
```

This prints row/column counts, series types, missing values, the date range, and sample rows. It is a diagnostic script, not an automated test suite.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| `EIA_API_KEY not found` | Confirm `.env` is in the project root and contains `EIA_API_KEY=...`; run commands from the project root. |
| `GCP_PROJECT_ID is missing from .env` | Add `GCP_PROJECT_ID` to the project-root `.env` file. |
| BigQuery credentials or permission error | Sign in with Application Default Credentials and confirm the identity has BigQuery dataset, load, and job permissions. |
| BigQuery table or project not found | The SQL currently hard-codes `malaysia-fuel-analytics`; configure that project or update the SQL project IDs consistently. |
| `File not found` while loading | Run all three ingestion commands first and confirm the Parquet files are in `data/raw/`. |
| Parquet validation fails | Review `data/raw/validation_report.csv` and `logs/validation.log`; check freshness, API availability, schema changes, and duplicate or invalid data. |
| Import or package error | Confirm VS Code selected `.venv`, activate it in the terminal, and run `python -m pip install -r requirements.txt`. |

## Data and credentials

The pipeline fetches data from external APIs and sends the resulting Parquet data to the configured BigQuery project when the warehouse commands are run. Review the source providers' terms and your organization's data-handling rules before sharing or publishing the results. Keep API keys and cloud credentials out of source control.
