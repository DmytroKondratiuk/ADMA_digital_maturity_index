"""Statistics mode of ADMA on data downloaded live from the official APIs.

Downloads the same series as data/raw/ directly from Eurostat and the Derzhstat data bank,
saves them to data/api_snapshot/<date>/ with the same layout, runs the same computation as
statistics_mode_local.py and reports every value that differs from the stored data.

Differences are expected over time: both agencies revise and add years. The paper is based
on data/raw/ (downloaded 9 October 2026).

Usage:  python scripts/statistics_mode_api.py
Output: data/api_snapshot/<date>/..., results/statistics_mode_api.json, printed comparison.
"""

import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_sources import (  # noqa: E402
    EUROSTAT_DATASETS, RAW_DATA, REPOSITORY_ROOT, UKRSTAT_FILES, download, eurostat_url, ukrstat_url)
from statistics_mode_local import compute_statistics_mode, print_table  # noqa: E402

UKRSTAT_ACCEPT = "application/vnd.sdmx.data+csv;version=2.0.0"


def download_snapshot(snapshot_directory):
    manifest = []
    (snapshot_directory / "eurostat").mkdir(parents=True, exist_ok=True)
    (snapshot_directory / "ukrstat" / "data_bank").mkdir(parents=True, exist_ok=True)
    for dataset in EUROSTAT_DATASETS:
        url = eurostat_url(dataset)
        path = snapshot_directory / "eurostat" / ("%s.csv" % dataset)
        path.write_bytes(download(url))
        manifest.append({"file": str(path.relative_to(REPOSITORY_ROOT)), "url": url})
        print("downloaded", path.relative_to(REPOSITORY_ROOT))
    for file_key in UKRSTAT_FILES:
        url = ukrstat_url(file_key)
        path = snapshot_directory / "ukrstat" / "data_bank" / ("%s.csv" % file_key)
        path.write_bytes(download(url, accept=UKRSTAT_ACCEPT))
        manifest.append({"file": str(path.relative_to(REPOSITORY_ROOT)), "url": url})
        print("downloaded", path.relative_to(REPOSITORY_ROOT))
    (snapshot_directory / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")


def compare(stored, fresh):
    differences = []
    compared_fields = ["ukraine_percent", "eu27_percent", "leader_country", "leader_percent", "ukraine_score", "eu27_score"]
    for stored_row, fresh_row in zip(stored["rows"], fresh["rows"]):
        for field in compared_fields:
            if stored_row[field] != fresh_row[field]:
                differences.append({"indicator": stored_row["name"], "field": field, "stored": stored_row[field], "api": fresh_row[field]})
    return differences


def main():
    snapshot_directory = REPOSITORY_ROOT / "data" / "api_snapshot" / date.today().isoformat()
    download_snapshot(snapshot_directory)
    fresh = compute_statistics_mode(snapshot_directory)
    stored = compute_statistics_mode(RAW_DATA)
    differences = compare(stored, fresh)
    output = {"snapshot": str(snapshot_directory.relative_to(REPOSITORY_ROOT)), "result": fresh, "differences_from_stored_data": differences}
    output_path = REPOSITORY_ROOT / "results" / "statistics_mode_api.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=1), encoding="utf-8")
    print_table(fresh, "\nStatistics mode, live API data (%s)" % date.today().isoformat())
    if differences:
        print("\nDifferences from the stored data used in the paper:")
        for difference in differences:
            print("  %(indicator)s, %(field)s: stored %(stored)s -> api %(api)s" % difference)
    else:
        print("\nNo differences: the live API data reproduce the stored data used in the paper.")
    print("Saved:", output_path)


if __name__ == "__main__":
    main()
