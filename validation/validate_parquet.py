
import logging
import time

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from datetime import datetime
from pathlib import Path


# ==========================================
# CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = BASE_DIR / "data" / "raw"
LOG_DIR = BASE_DIR / "logs"

REPORT_FILE = RAW_DIR / "validation_report.csv"
LOG_FILE = LOG_DIR / "validation.log"

RAW_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


# ==========================================
# LOGGING CONFIGURATION
# ==========================================

logger = logging.getLogger("parquet_validation")
logger.setLevel(logging.INFO)

if not logger.handlers:

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    file_handler = logging.FileHandler(
        LOG_FILE,
        encoding="utf-8"
    )

    console_handler = logging.StreamHandler()

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


# ==========================================
# VALIDATION RULES
# ==========================================

VALIDATION_RULES = {

    "crude_oil.parquet": {

        "required_columns": [
            "period",
            "series",
            "value",
            "units"
        ],

        "expected_arrow_types": {
            "period": "string",
            "series": "string",
            "value": "string",
            "units": "string"
        },

        "expected_physical_types": {
            "period": "BYTE_ARRAY",
            "series": "BYTE_ARRAY",
            "value": "BYTE_ARRAY",
            "units": "BYTE_ARRAY"
        },

        "date_columns": ["period"],

        "numeric_columns": ["value"],

        "not_null_columns": [
            "period",
            "series",
            "value",
            "units"
        ],

        "unique_columns": [
            "period",
            "series"
        ],

        "expected_values": {
            "series": ["RWTC"]
        },

        "freshness": {
            "date_column": "period",
            "max_age_days": 7
        }
    },


    "exchange_rates.parquet": {

        "required_columns": [
            "currency_code",
            "unit",
            "rate.date",
            "rate.buying_rate",
            "rate.selling_rate",
            "rate.middle_rate"
        ],

        "expected_arrow_types": {
            "currency_code": "string",
            "unit": "int64",
            "rate.date": "string",
            "rate.buying_rate": "double",
            "rate.selling_rate": "double",
            "rate.middle_rate": "double"
        },

        "expected_physical_types": {
            "currency_code": "BYTE_ARRAY",
            "unit": "INT64",
            "rate.date": "BYTE_ARRAY",
            "rate.buying_rate": "DOUBLE",
            "rate.selling_rate": "DOUBLE",
            "rate.middle_rate": "DOUBLE"
        },

        "date_columns": ["rate.date"],

        "numeric_columns": [
            "unit",
            "rate.buying_rate",
            "rate.selling_rate",
            "rate.middle_rate"
        ],

        "not_null_columns": [
            "currency_code",
            "unit",
            "rate.date",
            "rate.middle_rate"
        ],

        "unique_columns": [
            "currency_code",
            "rate.date"
        ],

        "expected_values": {},

        "freshness": {
            "date_column": "rate.date",
            "max_age_days": 7
        }
    },


    "fuel_prices.parquet": {

        "required_columns": [
            "date",
            "ron95",
            "ron97",
            "diesel"
        ],

        "expected_arrow_types": {
            "date": "string",
            "ron95": "double",
            "ron97": "double",
            "diesel": "double"
        },

        "expected_physical_types": {
            "date": "BYTE_ARRAY",
            "ron95": "DOUBLE",
            "ron97": "DOUBLE",
            "diesel": "DOUBLE"
        },

        "date_columns": ["date"],

        "numeric_columns": [
            "ron95",
            "ron97",
            "diesel"
        ],

        "not_null_columns": ["date"],

        "unique_columns": ["date"],

        "expected_values": {},

        "freshness": {
            "date_column": "date",
            "max_age_days": 14
        }
    }
}


# ==========================================
# HELPER: ERROR AND WARNING COLLECTION
# ==========================================

def add_error(errors, message):

    errors.append(message)


def add_warning(warnings, message):

    warnings.append(message)


# ==========================================
# 1. PHYSICAL DATA TYPE VALIDATION
# ==========================================

def validate_physical_types(parquet_file, rules):

    errors = []

    arrow_schema = parquet_file.schema_arrow
    parquet_schema = parquet_file.schema

    # Expected Arrow data types
    expected_arrow_types = rules.get(
        "expected_arrow_types", {}
    )

    for column, expected_type in expected_arrow_types.items():

        if column not in arrow_schema.names:
            continue

        actual_type = str(
            arrow_schema.field(column).type
        )

        if actual_type != expected_type:

            errors.append(
                f"{column}: Expected Arrow type "
                f"{expected_type}, got {actual_type}."
            )

    # Expected Parquet physical types
    expected_physical_types = rules.get(
        "expected_physical_types", {}
    )

    for column, expected_type in expected_physical_types.items():

        if column not in arrow_schema.names:
            continue

        column_index = arrow_schema.names.index(column)

        actual_type = parquet_schema.column(
            column_index
        ).physical_type

        if actual_type != expected_type:

            errors.append(
                f"{column}: Expected physical type "
                f"{expected_type}, got {actual_type}."
            )

    return errors


# ==========================================
# 2. DATAFRAME VALIDATION
# ==========================================

def validate_dataframe(df, rules):

    errors = []
    warnings = []

    # Check 1: Empty dataset
    if df.empty:

        errors.append("Dataset is empty.")

        return errors, warnings

    # Check 2: Required columns
    required_columns = rules["required_columns"]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:

        errors.append(
            f"Missing required columns: {missing_columns}"
        )

        return errors, warnings

    # Check 3: Null values
    for col in rules.get("not_null_columns", []):

        null_count = df[col].isna().sum()

        if null_count > 0:

            errors.append(
                f"{col}: {null_count} null values found."
            )

    # Check 4: Date validation
    parsed_dates = {}

    for col in rules.get("date_columns", []):

        dates = pd.to_datetime(
            df[col],
            errors="coerce"
        )

        parsed_dates[col] = dates

        invalid_count = (
            df[col].notna() & dates.isna()
        ).sum()

        if invalid_count > 0:

            errors.append(
                f"{col}: {invalid_count} invalid dates found."
            )

    # Check 5: Numeric validation
    for col in rules.get("numeric_columns", []):

        values = pd.to_numeric(
            df[col],
            errors="coerce"
        )

        invalid_count = (
            df[col].notna() & values.isna()
        ).sum()

        if invalid_count > 0:

            errors.append(
                f"{col}: {invalid_count} invalid numeric values."
            )

    # Check 6: Duplicate records
    unique_columns = rules.get("unique_columns", [])

    if unique_columns:

        duplicates = df.duplicated(
            subset=unique_columns
        ).sum()

        if duplicates > 0:

            errors.append(
                f"Found {duplicates} duplicate records "
                f"based on {unique_columns}."
            )

    # Check 7: Expected values
    expected_values = rules.get(
        "expected_values", {}
    )

    for col, expected in expected_values.items():

        if col not in df.columns:
            continue

        invalid_count = (
            df[col].notna() &
            ~df[col].isin(expected)
        ).sum()

        if invalid_count > 0:

            errors.append(
                f"{col}: {invalid_count} unexpected values. "
                f"Expected: {expected}."
            )

    return errors, warnings


# ==========================================
# 3. DATA FRESHNESS VALIDATION
# ==========================================

def validate_freshness(df, rules):

    errors = []
    warnings = []

    freshness_rules = rules.get("freshness")

    if not freshness_rules:
        return errors, warnings, None

    date_column = freshness_rules["date_column"]

    max_age_days = freshness_rules["max_age_days"]

    if date_column not in df.columns:

        errors.append(
            f"Freshness check failed: "
            f"{date_column} column not found."
        )

        return errors, warnings, None

    dates = pd.to_datetime(
        df[date_column],
        errors="coerce"
    ).dropna()

    if dates.empty:

        errors.append(
            f"Freshness check failed: "
            f"No valid dates in {date_column}."
        )

        return errors, warnings, None

    latest_date = dates.max().normalize()

    today = pd.Timestamp.now().normalize()

    age_days = (today - latest_date).days

    # Check future dates
    if age_days < -1:

        errors.append(
            f"Latest date {latest_date.date()} "
            f"is {abs(age_days)} days in the future."
        )

    # Check freshness threshold
    elif age_days > max_age_days:

        errors.append(
            f"Dataset is outdated. Latest date: "
            f"{latest_date.date()}, age: {age_days} days, "
            f"maximum allowed: {max_age_days} days."
        )

    else:

        logger.info(
            f"Freshness passed. Latest date: "
            f"{latest_date.date()}, age: {age_days} days."
        )

    return errors, warnings, latest_date


# ==========================================
# 4. SINGLE PARQUET VALIDATION
# ==========================================

def validate_single_file(file_path):

    start_time = time.perf_counter()

    checked_at = datetime.now().isoformat(
        timespec="seconds"
    )

    errors = []
    warnings = []

    row_count = 0
    file_size = 0
    latest_date = None

    logger.info("=" * 60)
    logger.info(f"Starting validation: {file_path.name}")

    try:

        # Check 1: File existence
        if not file_path.exists():

            raise FileNotFoundError(
                f"File does not exist: {file_path}"
            )

        # Check 2: File size
        file_size = file_path.stat().st_size

        if file_size == 0:

            raise ValueError(
                "Parquet file is empty."
            )

        # Check 3: Read Parquet metadata
        parquet_file = pq.ParquetFile(file_path)

        row_count = parquet_file.metadata.num_rows

        logger.info(f"File size: {file_size:,} bytes")
        logger.info(f"Total rows: {row_count}")

        # Check 4: Dataset rules
        rules = VALIDATION_RULES.get(file_path.name)

        if rules is None:

            warnings.append(
                "No validation rules configured."
            )

            status = "SKIPPED"

            logger.warning(
                f"No rules configured for {file_path.name}"
            )

            return build_result(
                file_path,
                status,
                row_count,
                file_size,
                latest_date,
                errors,
                warnings,
                checked_at,
                start_time
            )

        # Check 5: Physical data types
        type_errors = validate_physical_types(
            parquet_file,
            rules
        )

        errors.extend(type_errors)

        # Check 6: Read actual data
        df = pd.read_parquet(
            file_path,
            engine="pyarrow"
        )

        # Check 7: Data validation
        data_errors, data_warnings = validate_dataframe(
            df,
            rules
        )

        errors.extend(data_errors)
        warnings.extend(data_warnings)

        # Check 8: Freshness validation
        freshness_errors, freshness_warnings, latest_date = (
            validate_freshness(df, rules)
        )

        errors.extend(freshness_errors)
        warnings.extend(freshness_warnings)

        # Determine status
        status = "FAILED" if errors else "PASSED"

        if status == "PASSED":

            logger.info(
                f"VALIDATION PASSED: {file_path.name}"
            )

        else:

            logger.error(
                f"VALIDATION FAILED: {file_path.name}"
            )

            for error in errors:

                logger.error(error)

        for warning in warnings:

            logger.warning(warning)

        return build_result(
            file_path,
            status,
            row_count,
            file_size,
            latest_date,
            errors,
            warnings,
            checked_at,
            start_time
        )

    except Exception as error:

        logger.exception(
            f"Validation exception for {file_path.name}"
        )

        errors.append(str(error))

        return build_result(
            file_path,
            "FAILED",
            row_count,
            file_size,
            latest_date,
            errors,
            warnings,
            checked_at,
            start_time
        )


# ==========================================
# 5. BUILD VALIDATION RESULT
# ==========================================

def build_result(
    file_path,
    status,
    row_count,
    file_size,
    latest_date,
    errors,
    warnings,
    checked_at,
    start_time
):

    duration = round(
        time.perf_counter() - start_time,
        3
    )

    return {
        "file": file_path.name,
        "status": status,
        "rows": row_count,
        "file_size_bytes": file_size,
        "latest_date": (
            str(latest_date.date())
            if latest_date is not None
            else None
        ),
        "errors": " | ".join(errors),
        "warnings": " | ".join(warnings),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "checked_at": checked_at,
        "duration_seconds": duration
    }


# ==========================================
# 6. VALIDATE ALL PARQUET FILES
# ==========================================

def validate_all_files():

    logger.info("\nStarting multiple Parquet validation...")

    parquet_files = sorted(
        RAW_DIR.glob("*.parquet")
    )

    if not parquet_files:

        logger.warning("No Parquet files found.")

        return False

    results = []

    for file_path in parquet_files:

        result = validate_single_file(file_path)

        results.append(result)

    # Create validation report
    summary = pd.DataFrame(results)

    # Save CSV report
    summary.to_csv(
        REPORT_FILE,
        index=False
    )

    # Summary statistics
    passed = sum(
        result["status"] == "PASSED"
        for result in results
    )

    failed = sum(
        result["status"] == "FAILED"
        for result in results
    )

    skipped = sum(
        result["status"] == "SKIPPED"
        for result in results
    )

    logger.info("=" * 60)
    logger.info("PARQUET VALIDATION SUMMARY")
    logger.info("=" * 60)

    logger.info(f"Total files: {len(results)}")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Skipped: {skipped}")

    logger.info(
        f"Validation report saved: {REPORT_FILE}"
    )

    logger.info(
        f"Validation log saved: {LOG_FILE}"
    )

    return failed == 0 and skipped == 0


# ==========================================
# MAIN EXECUTION
# ==========================================

def main():

    success = validate_all_files()

    if not success:

        logger.error(
            "One or more Parquet files failed validation."
        )

        raise ValueError(
            "Parquet validation failed. "
            "Check validation_report.csv and validation.log."
        )

    logger.info(
        "All Parquet files passed validation!"
    )


if __name__ == "__main__":
    main()
