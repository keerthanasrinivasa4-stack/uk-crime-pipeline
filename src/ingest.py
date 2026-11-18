"""Step 1 (extract): download street-level crime data for each city and month.

Saves one JSON file per city and month in data/raw. Files that already exist are
skipped, so the script is safe to run again.  Usage: python src/ingest.py
"""
import json
import os
import time
from datetime import date

import requests

from config import (CITIES, MONTHS_BACK, PUBLISH_LAG_MONTHS, RAW_DATA_DIR, API_BASE_URL,
                    REQUEST_TIMEOUT_SECONDS, SLEEP_BETWEEN_REQUESTS_SECONDS, RETRIES,
                    RETRY_WAIT_SECONDS, MIN_RECORDS_PER_CITY_MONTH)


def last_n_months(n, lag=PUBLISH_LAG_MONTHS):
    """Return n 'YYYY-MM' strings, oldest first, starting `lag` months back."""
    year, month = date.today().year, date.today().month
    month -= lag
    months = []
    while len(months) < n:
        if month <= 0:
            month += 12
            year -= 1
        months.append(f"{year}-{month:02d}")
        month -= 1
    return list(reversed(months))


def fetch_crimes(lat, lng, month, retries=RETRIES, wait=RETRY_WAIT_SECONDS):
    """Return the list of crimes, or None if there is no data.
    Temporary problems (network errors, other statuses) are retried with a longer
    wait each time. A 404 or 503 means 'no data', so we skip without retrying."""
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(API_BASE_URL, params={"lat": lat, "lng": lng, "date": month},
                             timeout=REQUEST_TIMEOUT_SECONDS)
        except requests.RequestException:
            print(f"  attempt {attempt}: request failed")
        else:
            if r.status_code == 200:
                return r.json()
            if r.status_code in (404, 503):
                print(f"  {month}: no data (status {r.status_code}), skipping")
                return None
            print(f"  attempt {attempt}: status {r.status_code}")
        time.sleep(wait * attempt)
    return None


def main():
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    months = last_n_months(MONTHS_BACK)
    print(f"Fetching {len(CITIES)} cities x {len(months)} months...")
    saved = 0
    for name, (lat, lng) in CITIES.items():
        for month in months:
            path = os.path.join(RAW_DATA_DIR, f"{name.lower()}_{month}.json")
            if os.path.exists(path):
                continue
            data = fetch_crimes(lat, lng, month)
            time.sleep(SLEEP_BETWEEN_REQUESTS_SECONDS)
            if data is None:
                continue
            if len(data) < MIN_RECORDS_PER_CITY_MONTH:
                print(f"  WARNING: only {len(data)} records for {name} {month}")
            with open(path, "w") as f:
                json.dump({"city": name, "month": month, "records": data}, f)
            print(f"[{name}] {month}: saved {len(data)} records")
            saved += 1
    print(f"Done. {saved} new files saved to {RAW_DATA_DIR}")


if __name__ == "__main__":
    main()
