"""Download the statistics-mode data live from the official APIs and compare with the stored data.

Downloads the same slices as data/raw/eurostat/ict_c10_c12/ and data/raw/ukrstat/ict_c10_c12/ from the Eurostat API
and the Derzhstat data bank into data/api_snapshot/<date>/ with the same layout, rebuilds the comparison matrix, runs the statistics mode (Tables 5 and 6) and lists
every value that differs from the stored data. Differences are expected over time, because both agencies revise
data and add survey years. The paper is based on the stored files (downloaded 9 October 2026).

Usage:  python scripts/statistics_mode_api.py
Output: data/api_snapshot/<date>/..., results/statistics_mode_api.json (and statistics_mode_api_ua.json), printed comparison.
"""

import json
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_sources import (  # noqa: E402
    EUROSTAT_JSONSTAT_URL, EUROSTAT_SDMX_URL, MATRIX_PATH, REPOSITORY_ROOT, STATISTICS_FOLDER, UKRSTAT_CSV_ACCEPT, UKRSTAT_DATA_URL,
    UKRSTAT_STRUCTURE_ACCEPT, UKRSTAT_STRUCTURE_URL, build_matrix, download, eurostat_datasets, read_matrix,
    ukrstat_indicators, write_matrix)
from statistics_mode_local import TABLE_ROWS, compute_statistics_mode, print_table  # noqa: E402
from translations_ua import write_ukrainian_results  # noqa: E402

COMPARED_FIELDS = ["ADMI_base", "penalty", "ADMI", "level", "DM_I", "DM_S"]


def download_snapshot(raw_root):
    eurostat_directory = raw_root / "eurostat" / STATISTICS_FOLDER
    ukrstat_directory = raw_root / "ukrstat" / STATISTICS_FOLDER
    eurostat_directory.mkdir(parents=True, exist_ok=True)
    ukrstat_directory.mkdir(parents=True, exist_ok=True)
    for dataset in eurostat_datasets():
        (eurostat_directory / ("eurostat_%s.csv" % dataset)).write_text(
            download(EUROSTAT_SDMX_URL.format(dataset=dataset, indicator="")), encoding="utf-8")
        jsonstat = json.loads(download(EUROSTAT_JSONSTAT_URL.format(dataset=dataset)))
        (eurostat_directory / ("eurostat_%s_metadata_EU27.json" % dataset)).write_text(
            json.dumps(jsonstat, ensure_ascii=False, indent=1), encoding="utf-8")
        print("downloaded Eurostat", dataset)
    for indicator in ukrstat_indicators():
        time.sleep(2)  # be polite to the Derzhstat rate limiter
        (ukrstat_directory / ("ukrstat_%s.csv" % indicator)).write_text(
            download(UKRSTAT_DATA_URL.format(indicator=indicator), accept=UKRSTAT_CSV_ACCEPT), encoding="utf-8")
        print("downloaded Derzhstat", indicator)
    structure = json.loads(download(UKRSTAT_STRUCTURE_URL, accept=UKRSTAT_STRUCTURE_ACCEPT))
    dataflow = structure["data"]["dataflows"][0]
    (ukrstat_directory / "ukrstat_dataflow_annotations.json").write_text(json.dumps(
        {"id": dataflow["id"], "version": dataflow.get("version"), "names": dataflow.get("names"),
         "annotations": dataflow.get("annotations")}, ensure_ascii=False, indent=1), encoding="utf-8")


def compare(stored, fresh):
    differences = []
    for country in TABLE_ROWS:
        stored_row, fresh_row = stored["countries"][country], fresh["countries"][country]
        for layer, value in stored_row["layers"].items():
            if round(value, 6) != round(fresh_row["layers"].get(layer, float("nan")), 6):
                differences.append({"object": country, "field": layer, "stored": value, "api": fresh_row["layers"].get(layer)})
        for field in COMPARED_FIELDS:
            if round(stored_row[field], 6) != round(fresh_row[field], 6):
                differences.append({"object": country, "field": field, "stored": stored_row[field], "api": fresh_row[field]})
    for country, ranking in stored["ranking"].items():
        for field in ["ADMI_rank", "TOPSIS_rank"]:
            if ranking[field] != fresh["ranking"][country][field]:
                differences.append({"object": country, "field": field, "stored": ranking[field], "api": fresh["ranking"][country][field]})
    return differences


def main():
    snapshot = REPOSITORY_ROOT / "data" / "api_snapshot" / date.today().isoformat()
    download_snapshot(snapshot)
    fresh_matrix = build_matrix(snapshot)
    write_matrix(fresh_matrix, snapshot / "matrix.csv")
    fresh = compute_statistics_mode([{key: str(value) for key, value in row.items()} for row in fresh_matrix])
    stored = compute_statistics_mode(read_matrix(MATRIX_PATH))
    differences = compare(stored, fresh)
    output = {"snapshot": str(snapshot.relative_to(REPOSITORY_ROOT)), "differences_from_stored_data": differences, "result": fresh}
    output_path = REPOSITORY_ROOT / "results" / "statistics_mode_api.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=1), encoding="utf-8")
    ukrainian_path = write_ukrainian_results(output_path, output)
    print_table(fresh, "\nStatistics mode, live API data (%s)" % date.today().isoformat())
    if differences:
        print("\nDifferences from the stored data used in the paper:")
        for difference in differences:
            print("  %(object)s, %(field)s: stored %(stored)s -> api %(api)s" % difference)
    else:
        print("\nNo differences: the live API data reproduce the stored data used in the paper.")
    print("Saved:", output_path)
    print("Saved:", ukrainian_path)


if __name__ == "__main__":
    main()
