"""Tiny tests for the cleaning rules. Run:  python tests/test_clean.py"""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from transform_load import clean  # noqa: E402


def row(pid, category, outcome=None, outcome_date=None, lat="51.5", lng="-0.1"):
    return {"persistent_id": pid, "category": category, "city": "London", "month": "2026-06",
            "latitude": lat, "longitude": lng, "street_name": "On or near X",
            "location_type": "Force", "outcome_category": outcome, "outcome_date": outcome_date}


def test_clean_rules():
    df = pd.DataFrame([
        row("a", "violent-crime", "Under investigation", "2026-06"),
        row("a", "violent-crime", "Under investigation", "2026-06"),   # exact copy: dropped
        row("b", "other-theft", "Awaiting court outcome", "2026-07"),
        row("b", "other-theft", "Under investigation", "2026-06"),      # older outcome: dropped
        row("c", "violent-crime", "Unable to prosecute suspect", "2026-07"),
        row("c", "public-order", "Under investigation", "2026-07"),     # different category: kept
        row("d", "burglary"),                                            # blank outcome: label added
        row("e", "burglary", lat=None, lng=None),                        # no coordinates: dropped
    ])
    out, stats = clean(df)
    assert stats["loaded"] == 8
    assert stats["after_exact_copies"] == 7
    assert stats["after_repeat_outcomes"] == 6
    assert stats["final"] == 5
    kept_b = out[out["persistent_id"] == "b"]
    assert len(kept_b) == 1 and kept_b.iloc[0]["outcome_category"] == "Awaiting court outcome"
    assert len(out[out["persistent_id"] == "c"]) == 2
    assert out[out["persistent_id"] == "d"].iloc[0]["outcome_category"] == "No outcome recorded yet"
    assert set(out["category"]) <= {"Violent Crime", "Other Theft", "Public Order", "Burglary"}
    print("All cleaning tests passed.")


if __name__ == "__main__":
    test_clean_rules()
