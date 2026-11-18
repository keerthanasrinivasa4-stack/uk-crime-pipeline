# UK Street Crime Data Pipeline (version 2)

A small, automated data pipeline: Police open data API -> Python and pandas -> Google BigQuery -> Power BI.

## What it does
1. `src/ingest.py` downloads street-level crimes for five English cities, 12 months (one JSON file per city and month). It retries temporary errors with a growing wait and skips months with no data (404 or 503).
2. `src/transform_load.py` cleans the data, runs quality checks, writes `data/crimes_clean.csv` and loads BigQuery (full refresh).
3. `.github/workflows/pipeline.yml` runs the tests and the pipeline every Monday, using GitHub Secrets for the Google credentials.

## Cleaning rules, and the evidence for them
- Rows identical in every column are plain copies and are dropped (70 in the first run).
- The same crime ID and category can repeat with different outcomes: keep the latest outcome.
- The same ID with a different category is kept, because it may be separate offences (27 IDs).
- Blank outcomes get the label "No outcome recorded yet". Rows without coordinates are dropped.

## Known limits
- The API covers England, Wales and Northern Ireland only. Police Scotland publishes no data to it, and Greater Manchester supplies almost none. Version 1 used Edinburgh, Glasgow and Manchester and returned almost nothing for them, which is why version 2 uses English cities.
- Each point returns crimes within about a mile of the city centre, so results are not whole-city figures.
- Counts are not rates per person, so do not compare cities by size.
- Possible next steps: explicit table schema, incremental loads, alerts on failed runs.

## Run it
    pip install -r requirements.txt
    python run_pipeline.py --no-bigquery      # local CSV only
    python tests/test_clean.py                # cleaning tests
