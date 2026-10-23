"""Statistics mode of ADMA on official data (proposition P4; Table 5 and Supplementary Table S3 of the paper).

Food processing (NACE C10-C12, enterprises 10+): EU-27, Germany, nine CEE countries and Ukraine.
  * equation (6) with P_min = 0: every indicator is divided by the value of the EU leader;
  * layer score = mean of its indicators; ADMI_base = mean of the five layers C, L1-L4 (equation 3);
  * weak-link penalty and ADMI with the calibrated parameters (equations 4-5); level by Table 2;
  * DM_I and DM_S are computed separately, outside the index;
  * independent check: TOPSIS (Hwang and Yoon, 1981) on the same five layers with entropy and equal weights;
  * proxy robustness: ADMI on the strict set without weak proxies, and with each weak proxy left out.
The ranking covers the nine CEE countries and Ukraine; EU-27 and Germany are reference rows.

Reads data/raw/eurostat/ict_c10_c12/ and data/raw/ukrstat/ict_c10_c12/ (the stored API responses), rebuilds the comparison matrix and checks that it is
identical to data/matrix.csv. Works offline.

Usage:  python scripts/statistics_mode_local.py
Output: results/statistics_mode_local.json and a printed version of Table 5.
"""

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from adma_index import CALIBRATED_PARAMETERS, maturity_level, penalty  # noqa: E402
from data_sources import (  # noqa: E402
    CEE_COUNTRIES, EU_AGGREGATE, LAYERS, MATRIX_PATH, OUTSIDE_INDEX, RAW_DATA, REFERENCE_COUNTRY,
    REPOSITORY_ROOT, STATEMENT, STRENGTH, build_matrix, parse_value, read_matrix)

TABLE_ROWS = [EU_AGGREGATE, REFERENCE_COUNTRY] + CEE_COUNTRIES + ["UA"]
RANKED = CEE_COUNTRIES + ["UA"]
COUNTRY_NAMES = {"EU27_2020": "EU-27", "DE": "Germany", "PL": "Poland", "HU": "Hungary", "RO": "Romania",
                 "CZ": "Czechia", "SK": "Slovakia", "LT": "Lithuania", "LV": "Latvia", "EE": "Estonia",
                 "BG": "Bulgaria", "UA": "Ukraine"}
RESULTS_PATH = REPOSITORY_ROOT / "results" / "statistics_mode_local.json"


def indicator_scores(matrix_rows):
    """Equation (6) with P_min = 0 for every indicator used by the statistics mode: {indicator: {country: score}}."""
    used = {code for codes in list(LAYERS.values()) + list(OUTSIDE_INDEX.values()) for code in codes}
    scores = {}
    for row in matrix_rows:
        if row["pair_id"] not in used:
            continue
        leader = parse_value(row["leader_value"])
        scores[row["pair_id"]] = {}
        for country in TABLE_ROWS:
            value = parse_value(row["%s_value" % country])
            scores[row["pair_id"]][country] = value / leader if value is not None else None
    return scores


def mean(values):
    present = [value for value in values if value is not None]
    return sum(present) / len(present) if present else None


def admi_table(scores, layers, countries):
    """Layer scores, ADMI_base, penalty, ADMI and level for each country; layers without indicators are dropped."""
    alpha, delta = CALIBRATED_PARAMETERS["alpha"], CALIBRATED_PARAMETERS["delta"]
    table = {}
    for country in countries:
        layer_scores = {layer: mean([scores[code][country] for code in codes]) for layer, codes in layers.items()}
        layer_scores = {layer: score for layer, score in layer_scores.items() if score is not None}
        base_index = sum(layer_scores.values()) / len(layer_scores)
        weakest = min(layer_scores.values())
        penalty_value = float(penalty(weakest, alpha, delta))
        final_index = base_index * penalty_value
        table[country] = {
            "layers": layer_scores, "ADMI_base": base_index, "DM_min": weakest,
            "weakest_layer": min(layer_scores, key=layer_scores.get), "penalty": penalty_value, "ADMI": final_index,
            "level_base": int(maturity_level([base_index])[0]), "level": int(maturity_level([final_index])[0]),
        }
    return table


def entropy_weights(layer_table, countries, layers):
    """Entropy method: a layer on which the countries differ more gets a higher weight."""
    divergence = {}
    for layer in layers:
        values = [layer_table[country][layer] for country in countries]
        total = sum(values)
        shares = [value / total for value in values]
        entropy = -sum(share * math.log(share) for share in shares if share > 0) / math.log(len(values))
        divergence[layer] = 1 - entropy
    total_divergence = sum(divergence.values())
    return {layer: divergence[layer] / total_divergence for layer in layers}


def topsis(layer_table, countries, layers, weights):
    """Closeness to the ideal solution (Hwang and Yoon, 1981) with vector normalisation."""
    norms = {layer: math.sqrt(sum(layer_table[country][layer] ** 2 for country in countries)) for layer in layers}
    weighted = {country: {layer: weights[layer] * layer_table[country][layer] / norms[layer] for layer in layers}
                for country in countries}
    ideal = {layer: max(weighted[country][layer] for country in countries) for layer in layers}
    anti_ideal = {layer: min(weighted[country][layer] for country in countries) for layer in layers}
    closeness = {}
    for country in countries:
        to_ideal = math.sqrt(sum((weighted[country][layer] - ideal[layer]) ** 2 for layer in layers))
        to_anti_ideal = math.sqrt(sum((weighted[country][layer] - anti_ideal[layer]) ** 2 for layer in layers))
        closeness[country] = to_anti_ideal / (to_ideal + to_anti_ideal)
    return closeness


def ranks(values):
    order = sorted(values, key=values.get, reverse=True)
    return {country: position + 1 for position, country in enumerate(order)}


def spearman(first_ranks, second_ranks):
    countries = list(first_ranks)
    count = len(countries)
    return 1 - 6 * sum((first_ranks[country] - second_ranks[country]) ** 2 for country in countries) / (count * (count ** 2 - 1))


def pearson(first, second):
    countries = list(first)
    mean_first = sum(first.values()) / len(countries)
    mean_second = sum(second.values()) / len(countries)
    covariance = sum((first[country] - mean_first) * (second[country] - mean_second) for country in countries)
    spread_first = math.sqrt(sum((first[country] - mean_first) ** 2 for country in countries))
    spread_second = math.sqrt(sum((second[country] - mean_second) ** 2 for country in countries))
    return covariance / (spread_first * spread_second)


def compare_variant(reference, variant):
    reference_ranks = ranks({country: reference[country]["ADMI"] for country in RANKED})
    variant_ranks = ranks({country: variant[country]["ADMI"] for country in RANKED})
    return {
        "spearman_with_full": round(spearman(reference_ranks, variant_ranks), 3),
        "max_rank_shift": max(abs(reference_ranks[country] - variant_ranks[country]) for country in RANKED),
        "countries_with_rank_shift": [country for country in RANKED if reference_ranks[country] != variant_ranks[country]],
        "level_agreement": round(sum(reference[country]["level"] == variant[country]["level"] for country in RANKED) / len(RANKED), 3),
        "countries_with_level_change": [country for country in RANKED if reference[country]["level"] != variant[country]["level"]],
        "ukraine_rank": variant_ranks["UA"],
        "ukraine_level": variant["UA"]["level"],
        "ADMI": {country: round(variant[country]["ADMI"], 3) for country in RANKED},
        "ranks": variant_ranks,
    }


def proxy_robustness(scores, full):
    """Supplementary Table S3: strict set without weak proxies and leave-one-out of each weak proxy."""
    index_codes = [code for codes in LAYERS.values() for code in codes]
    strict_layers = {layer: [code for code in codes if STRENGTH[code] != "proxy"] for layer, codes in LAYERS.items()}
    strict_layers = {layer: codes for layer, codes in strict_layers.items() if codes}
    leave_one_out = {}
    for weak_proxy in [code for code in index_codes if STRENGTH[code] == "proxy"]:
        reduced = {layer: [code for code in codes if code != weak_proxy] for layer, codes in LAYERS.items()}
        reduced = {layer: codes for layer, codes in reduced.items() if codes}
        leave_one_out[weak_proxy] = compare_variant(full, admi_table(scores, reduced, RANKED))
    return {
        "counts_in_index": {grade: sum(1 for code in index_codes if STRENGTH[code] == grade) for grade in ("direct", "acceptable", "proxy")},
        "strict_set": dict(compare_variant(full, admi_table(scores, strict_layers, RANKED)),
                           layers=strict_layers, layers_dropped=[layer for layer in LAYERS if layer not in strict_layers]),
        "leave_one_out": leave_one_out,
        "leave_one_out_min_spearman": min(item["spearman_with_full"] for item in leave_one_out.values()),
        "leave_one_out_max_rank_shift": max(item["max_rank_shift"] for item in leave_one_out.values()),
    }


def compute_statistics_mode(matrix_rows):
    scores = indicator_scores(matrix_rows)
    table = admi_table(scores, LAYERS, TABLE_ROWS)
    for country in TABLE_ROWS:
        for name, codes in OUTSIDE_INDEX.items():
            table[country]["DM_" + name] = mean([scores[code][country] for code in codes])
    layer_table = {country: table[country]["layers"] for country in RANKED}
    weights = entropy_weights(layer_table, RANKED, list(LAYERS))
    closeness = topsis(layer_table, RANKED, list(LAYERS), weights)
    equal_weights = {layer: 1 / len(LAYERS) for layer in LAYERS}
    admi_ranks = ranks({country: table[country]["ADMI"] for country in RANKED})
    base_ranks = ranks({country: table[country]["ADMI_base"] for country in RANKED})
    topsis_ranks = ranks(closeness)
    topsis_equal_ranks = ranks(topsis(layer_table, RANKED, list(LAYERS), equal_weights))
    years = {row["pair_id"]: {"eurostat": row["eurostat_year_used"], "ukrstat": row["ukrstat_year_used"],
                              "leader": row["leader_country"], "leader_value": parse_value(row["leader_value"])}
             for row in matrix_rows if row["pair_id"] in scores}
    return {
        "parameters": dict(CALIBRATED_PARAMETERS, normalisation="P / value of the EU-27 member state with the highest published value (P_min = 0)"),
        "layers": LAYERS, "outside_index": OUTSIDE_INDEX, "statement": {code: STATEMENT[code] for code in scores},
        "strength": {code: STRENGTH[code] for code in scores}, "years_and_leaders": years,
        "indicator_scores": scores,
        "countries": table,
        "ranking": {country: {"ADMI_rank": admi_ranks[country], "TOPSIS_closeness": closeness[country],
                              "TOPSIS_rank": topsis_ranks[country], "TOPSIS_equal_weights_rank": topsis_equal_ranks[country]}
                    for country in RANKED},
        "entropy_weights": weights,
        "spearman_ADMI_base": spearman(admi_ranks, base_ranks),
        "spearman_ADMI_TOPSIS": spearman(admi_ranks, topsis_ranks),
        "pearson_ADMI_TOPSIS_values": pearson({country: table[country]["ADMI"] for country in RANKED}, closeness),
        "spearman_TOPSIS_entropy_vs_equal": spearman(topsis_ranks, topsis_equal_ranks),
        "proxy_robustness": proxy_robustness(scores, table),
    }


def print_table(result, title):
    print(title)
    print("%-10s %5s %5s %5s %5s %5s %8s %7s %7s %5s %5s %5s %6s" % (
        "Object", "C", "L1", "L2", "L3", "L4", "ADMIbase", "P", "ADMI", "Level", "DM_I", "Rank", "TOPSIS"))
    for country in TABLE_ROWS:
        row = result["countries"][country]
        ranking = result["ranking"].get(country, {})
        print("%-10s %5.2f %5.2f %5.2f %5.2f %5.2f %8.3f %7.3f %7.3f %5d %5.2f %5s %6s" % (
            COUNTRY_NAMES[country], row["layers"]["C"], row["layers"]["L1"], row["layers"]["L2"], row["layers"]["L3"],
            row["layers"]["L4"], row["ADMI_base"], row["penalty"], row["ADMI"], row["level"], row["DM_I"],
            ranking.get("ADMI_rank", "-"), ranking.get("TOPSIS_rank", "-")))
    print("Spearman ADMI-ADMI_base %.3f, ADMI-TOPSIS %.3f, Pearson %.3f, TOPSIS entropy vs equal weights %.3f" % (
        result["spearman_ADMI_base"], result["spearman_ADMI_TOPSIS"], result["pearson_ADMI_TOPSIS_values"], result["spearman_TOPSIS_entropy_vs_equal"]))
    robustness = result["proxy_robustness"]
    print("Strict set: Spearman %.3f, level changes %s | leave-one-out: min Spearman %.3f, max rank shift %d" % (
        robustness["strict_set"]["spearman_with_full"], robustness["strict_set"]["countries_with_level_change"],
        robustness["leave_one_out_min_spearman"], robustness["leave_one_out_max_rank_shift"]))


def main():
    rebuilt = build_matrix(RAW_DATA)
    stored = read_matrix(MATRIX_PATH)
    if [{key: str(value) for key, value in row.items()} for row in rebuilt] != stored:
        raise SystemExit("data/matrix.csv differs from the matrix rebuilt from data/raw/{eurostat,ukrstat}/ict_c10_c12/")
    result = compute_statistics_mode(stored)
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print_table(result, "Statistics mode, stored data (data/raw/{eurostat,ukrstat}/ict_c10_c12, downloaded 9 October 2026)")
    print("Saved:", RESULTS_PATH)


if __name__ == "__main__":
    main()
