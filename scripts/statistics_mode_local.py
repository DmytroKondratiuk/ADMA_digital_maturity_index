"""Statistics mode of ADMA on the stored raw data (Table 7 of the paper).

Reads only files in data/raw/ (no internet needed) and reproduces the published numbers.

Usage:  python scripts/statistics_mode_local.py
Output: results/statistics_mode_local.json and a printed version of Table 7.
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from adma_index import CALIBRATED_PARAMETERS, LAYERS, statistics_mode_score  # noqa: E402
from data_sources import RAW_DATA, REPOSITORY_ROOT, STATISTICS_MODE_INDICATORS, eurostat_values, read_csv, ukrstat_value  # noqa: E402


def compute_statistics_mode(raw_directory):
    """Compute Table 7 from a directory laid out like data/raw/ (eurostat/*.csv, ukrstat/data_bank/*.csv)."""
    raw_directory = Path(raw_directory)
    eurostat_cache = {}
    ukrstat_cache = {}
    rows = []
    for indicator in STATISTICS_MODE_INDICATORS:
        eurostat_spec = indicator["eurostat"]
        ukrstat_spec = indicator["ukrstat"]
        if eurostat_spec["dataset"] not in eurostat_cache:
            eurostat_cache[eurostat_spec["dataset"]] = read_csv(raw_directory / "eurostat" / ("%s.csv" % eurostat_spec["dataset"]))
        if ukrstat_spec["file"] not in ukrstat_cache:
            ukrstat_cache[ukrstat_spec["file"]] = read_csv(raw_directory / "ukrstat" / "data_bank" / ("%s.csv" % ukrstat_spec["file"]))
        countries, eu_average, missing = eurostat_values(eurostat_cache[eurostat_spec["dataset"]], eurostat_spec["indicator"], eurostat_spec["year"])
        leader = max(countries, key=countries.get)
        ukraine_value, ukraine_updated = ukrstat_value(
            ukrstat_cache[ukrstat_spec["file"]], ukrstat_spec["breakdown_category"], ukrstat_spec["breakdown"], ukrstat_spec["year"])
        rows.append({
            "name": indicator["name"],
            "layer": indicator["layer"],
            "statement": indicator["statement"],
            "eurostat_indicator": eurostat_spec["indicator"],
            "ukraine_percent": ukraine_value,
            "ukraine_year": ukrstat_spec["year"],
            "ukraine_data_updated": ukraine_updated,
            "eu27_percent": eu_average,
            "eurostat_year": eurostat_spec["year"],
            "leader_country": leader,
            "leader_percent": countries[leader],
            "eu27_countries_without_value": missing,
            "ukraine_score": round(statistics_mode_score(ukraine_value, countries[leader]), 3),
            "eu27_score": round(statistics_mode_score(eu_average, countries[leader]), 3),
        })
    profile = {}
    for layer in LAYERS:
        layer_rows = [row for row in rows if row["layer"] == layer]
        if layer_rows:
            profile[layer] = {
                "ukraine": round(float(np.mean([row["ukraine_score"] for row in layer_rows])), 3),
                "eu27": round(float(np.mean([row["eu27_score"] for row in layer_rows])), 3),
            }
    delta = CALIBRATED_PARAMETERS["delta"]
    return {
        "rows": rows,
        "layer_profile": profile,
        "layers_not_measured": [layer for layer in LAYERS if layer not in profile],
        "ukraine_layers_below_delta": [layer for layer, scores in profile.items() if scores["ukraine"] < delta],
        "eu27_layers_below_delta": [layer for layer, scores in profile.items() if scores["eu27"] < delta],
        "note": "L1 has no common indicator in Derzhstat and Eurostat; agriculture (NACE A) is not covered by either survey.",
    }


def print_table(result, title):
    print(title)
    print("%-5s %-32s %14s %14s %14s %8s %8s" % ("Layer", "Indicator", "Ukraine %", "EU27 %", "Leader %", "DM UA", "DM EU"))
    for row in result["rows"]:
        print("%-5s %-32s %8.1f (%s) %8.2f (%s) %7.2f (%s) %8.3f %8.3f" % (
            row["layer"], row["name"], row["ukraine_percent"], row["ukraine_year"], row["eu27_percent"], row["eurostat_year"],
            row["leader_percent"], row["leader_country"], row["ukraine_score"], row["eu27_score"]))
    print("Layer profile:", ", ".join("%s UA %.3f / EU %.3f" % (layer, scores["ukraine"], scores["eu27"]) for layer, scores in result["layer_profile"].items()))
    print("Not measured:", ", ".join(result["layers_not_measured"]))


def main():
    result = compute_statistics_mode(RAW_DATA)
    output_path = REPOSITORY_ROOT / "results" / "statistics_mode_local.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print_table(result, "Statistics mode, stored raw data (data/raw)")
    print("Saved:", output_path)


if __name__ == "__main__":
    main()
