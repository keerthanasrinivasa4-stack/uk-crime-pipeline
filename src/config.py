"""Central settings for the UK Street Crime pipeline (version 2)."""
import os

# City centre points. The API returns crimes within about 1 mile of each point.
# Only cities in England, Wales and Northern Ireland work: Police Scotland does
# not publish to data.police.uk, and Greater Manchester supplies almost nothing.
CITIES = {
    "London": (51.509865, -0.118092),
    "Birmingham": (52.489471, -1.898575),
    "Leeds": (53.800755, -1.549077),
    "Bristol": (51.454514, -2.587910),
    "Liverpool": (53.408371, -2.991573),
}

MONTHS_BACK = 12
PUBLISH_LAG_MONTHS = 3   # the API publishes about 2 to 3 months late

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_CSV_PATH = os.path.join(BASE_DIR, "data", "crimes_clean.csv")

API_BASE_URL = "https://data.police.uk/api/crimes-street/all-crime"
REQUEST_TIMEOUT_SECONDS = 15
SLEEP_BETWEEN_REQUESTS_SECONDS = 0.3
RETRIES = 3
RETRY_WAIT_SECONDS = 2
MIN_RECORDS_PER_CITY_MONTH = 100   # below this we print a coverage warning

# BigQuery settings come from environment variables (GitHub Secrets), never from code.
BQ_PROJECT_ID = os.environ.get("BQ_PROJECT_ID", "")
BQ_DATASET = os.environ.get("BQ_DATASET", "uk_crime")
BQ_TABLE = os.environ.get("BQ_TABLE", "street_crimes")
