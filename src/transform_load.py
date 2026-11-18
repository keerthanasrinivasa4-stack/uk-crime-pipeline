"""Steps 2 and 3 (transform, load): clean the raw files, check quality, save a CSV
and (optionally) load the table into BigQuery.

Usage:  python src/transform_load.py --no-bigquery     (CSV only)
        python src/transform_load.py                   (CSV and BigQuery)
"""
import argparse
import glob
import json
import os

import pandas as pd

from config import (RAW_DATA_DIR, PROCESSED_CSV_PATH, BQ_PROJECT_ID, BQ_DATASET, BQ_TABLE,
                    MIN_RECORDS_PER_CITY_MONTH)


def load_raw_files():
    """Read every raw JSON file into one flat pandas table."""
    rows = []
    files = glob.glob(os.path.join(RAW_DATA_DIR, "*.json"))
    print(f"Reading {len(files)} raw files...")
    for path in files:
        with open(path) as f:
            payload = json.load(f)
        city, month = payload["city"], payload["month"]
        for record in payload["records"]:
            location = record.get("location") or {}
            street = location.get("street") or {}
            outcome = record.get("outcome_status") or {}
            persistent_id = record.get("persistent_id") or record.get("id")
            rows.append({
                "persistent_id": str(persistent_id) if persistent_id is not None else None,
                "category": record.get("category"),
                "city": city,
                "month": month,
                "latitude": location.get("latitude"),
                "longitude": location.get("longitude"),
                "street_name": street.get("name"),
                "location_type": record.get("location_type"),
                "outcome_category": outcome.get("category"),
                "outcome_date": outcome.get("date"),
            })
    return pd.DataFrame(rows)


def clean(df):
    """Clean the table. Returns the cleaned table and a dictionary of row counts."""
    stats = {"loaded": len(df)}

    # 1. Rows identical in every column are plain copies: drop them.
    df = df.drop_duplicates()
    stats["after_exact_copies"] = len(df)

    # 2. The same crime (ID) and category can appear more than once with different
    #    outcomes. Keep the row with the latest outcome date. Rows with the same ID
    #    but a DIFFERENT category are kept, because they may be separate offences.
    df = df.sort_values("outcome_date", ascending=False, na_position="last")
    df = df.drop_duplicates(subset=["persistent_id", "category"], keep="first")
    stats["after_repeat_outcomes"] = len(df)

    # 3. Types and labels.
    df = df.copy()
    df["category"] = df["category"].str.replace("-", " ").str.title()
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["month"] = pd.to_datetime(df["month"], format="%Y-%m")
    df["outcome_category"] = df["outcome_category"].fillna("No outcome recorded yet")
    df["outcome_date"] = df["outcome_date"].fillna("")

    # 4. Rows without coordinates or category cannot be mapped or counted.
    df = df.dropna(subset=["latitude", "longitude", "category"])
    stats["final"] = len(df)
    return df.reset_index(drop=True), stats


def quality_checks(df):
    """Fail loudly if the cleaned table looks wrong."""
    assert not df.duplicated(subset=["persistent_id", "category"]).any(), "duplicate crime rows remain"
    assert df["category"].notna().all(), "missing category"
    assert df["latitude"].notna().all() and df["longitude"].notna().all(), "missing coordinates"
    per_city = df.groupby("city").size()
    print("Rows per city:")
    print(per_city.to_string())
    monthly = df.groupby(["city", "month"]).size()
    low = monthly[monthly < MIN_RECORDS_PER_CITY_MONTH]
    if len(low):
        print("WARNING: city-months with very few records:")
        print(low.to_string())
    print("Quality checks passed.")


def load_to_bigquery(df):
    if not BQ_PROJECT_ID:
        print("BQ_PROJECT_ID not set, skipping the BigQuery load (CSV still written).")
        return
    from google.cloud import bigquery
    client = bigquery.Client(project=BQ_PROJECT_ID)
    dataset_ref = f"{BQ_PROJECT_ID}.{BQ_DATASET}"
    table_ref = f"{dataset_ref}.{BQ_TABLE}"
    client.create_dataset(dataset_ref, exists_ok=True)
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE", autodetect=True)
    client.load_table_from_dataframe(df, table_ref, job_config=job_config).result()
    print(f"Loaded {len(df)} rows into {table_ref} (full refresh)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-bigquery", action="store_true")
    args = parser.parse_args()

    df = load_raw_files()
    if df.empty:
        print("No data found. Run ingest.py first.")
        raise SystemExit(1)
    df, stats = clean(df)
    print(f"Row counts: {stats}")
    quality_checks(df)
    os.makedirs(os.path.dirname(PROCESSED_CSV_PATH), exist_ok=True)
    df.to_csv(PROCESSED_CSV_PATH, index=False)
    print(f"Wrote {PROCESSED_CSV_PATH}")
    if not args.no_bigquery:
        load_to_bigquery(df)


if __name__ == "__main__":
    main()
