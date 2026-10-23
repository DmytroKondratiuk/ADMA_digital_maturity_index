"""Computational experiment on the properties of the ADMI index (Sections 3 and 4 of the paper).

Checks three propositions on questionnaire responses generated at the item level:
  P1  the weak-link penalty changes the maturity level, not only the index value, for an analytically
      bounded region of profiles (equation 7);
  P2  a scalar that averages DM_I in hides integration gaps that the pair (ADMI, DM_I) reveals;
  P3  the level classification is robust to the penalty parameters alpha and delta.
It also compares ADMI with other aggregation rules, including the Mazziotta-Pareto index (Table 3).
P4 (statistics mode on official data) is checked by statistics_mode_local.py.

The profiles are synthetic: they describe the behaviour of the instrument over the whole
response space, not the state of real enterprises.

Usage:  python scripts/simulation_experiment.py
Output: results/simulation_experiment.json and a printed summary.
Runtime: about one minute (2 x 100 000 profiles, 99 parameter combinations).
"""

import json
import platform
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from adma_index import (  # noqa: E402
    CALIBRATED_PARAMETERS, INITIAL_PARAMETERS, ITEMS_INTEGRATION, ITEMS_PER_LAYER, ITEMS_STRATEGY,
    MODEL_ADJUSTED_BOUNDS, THEORETICAL_BOUNDS, admi, maturity_level, mazziotta_pareto, penalty)

from generate_profiles import GENERATED_DATA, RESPONSE_SCENARIOS, SEED, column_names  # noqa: E402

RESULTS_PATH = Path(__file__).resolve().parent.parent / "results" / "simulation_experiment.json"


def load_profiles(scenario_name):
    """Read stored responses (data/generated/) and compute block scores, equations (1)-(2)."""
    path = GENERATED_DATA / ("profiles_%s.csv" % scenario_name)
    responses = np.loadtxt(str(path), delimiter=",", skiprows=1, dtype=np.int64)[:, 1:]
    names = column_names()

    def block_score(prefix, item_count):
        start = names.index("%s_1" % prefix)
        return ((responses[:, start:start + item_count] - 1) / 4).mean(axis=1)

    layers = np.column_stack([block_score(layer, item_count) for layer, item_count in ITEMS_PER_LAYER.items()])
    return {"layers": layers, "integration": block_score("I", ITEMS_INTEGRATION), "strategy": block_score("S", ITEMS_STRATEGY)}


def level_change_summary(layers, alpha, delta, bounds=THEORETICAL_BOUNDS):
    """P1: how often the penalty applies and how often it changes the level (Supplementary Table S2)."""
    base_index, final_index = admi(layers, alpha, delta)
    base_level = maturity_level(base_index, bounds)
    final_level = maturity_level(final_index, bounds)
    penalised = penalty(layers.min(axis=1), alpha, delta) < 1.0
    changed = final_level != base_level
    transitions = {}
    for level in range(2, 6):
        mask = base_level == level
        if mask.any():
            transitions["%d->%d" % (level, level - 1)] = round(float((changed & mask).sum() / mask.sum()), 4)
    return {
        "share_penalised": round(float(penalised.mean()), 4),
        "share_level_changed": round(float(changed.mean()), 4),
        "share_level_changed_among_penalised": round(float(changed[penalised].mean()), 4) if penalised.any() else 0.0,
        "max_level_drop": int((base_level - final_level).max()),
        "mean_index_reduction": round(float((base_index - final_index).mean()), 4),
        "max_index_reduction": round(float((base_index - final_index).max()), 4),
        "share_changed_from_level": transitions,
    }


def residual_masking(layers, alpha, delta):
    """P1: how much masking the penalty leaves. Among profiles at level 3 or higher by ADMI, the share whose
    weakest layer is below delta (penalised but kept at the level) and the share with a practically failed
    weakest layer (DM_min <= 1/12: all answers 1 except at most one 2)."""
    _, final_index = admi(layers, alpha, delta)
    high_level = maturity_level(final_index) >= 3
    weakest = layers.min(axis=1)
    return {
        "share_level_3plus": round(float(high_level.mean()), 4),
        "share_of_level_3plus_with_weakest_below_delta": round(float((high_level & (weakest < delta)).sum() / high_level.sum()), 4),
        "share_of_level_3plus_with_failed_weakest_layer": round(float((high_level & (weakest <= 1 / 12 + 1e-9)).sum() / high_level.sum()), 4),
    }


def boundary_band(alpha, delta, bounds=THEORETICAL_BOUNDS):
    """Equation (7): the level drops across bound b iff b < ADMI_base <= b / P(DM_min)."""
    layer_minimum_grid = np.round(np.arange(0.0, delta + 1e-9, 0.025), 3)
    bands = []
    for bound in bounds:
        for layer_minimum in layer_minimum_grid:
            penalty_value = float(penalty(layer_minimum, alpha, delta))
            # ADMI_base cannot exceed (4 * 1 + DM_min) / 5 when the weakest layer equals DM_min
            feasible_upper = min(bound / penalty_value, (4.0 + layer_minimum) / 5.0)
            bands.append({
                "bound": bound,
                "layer_minimum": float(layer_minimum),
                "penalty": round(penalty_value, 4),
                "base_index_from": bound,
                "base_index_to": round(feasible_upper, 4),
                "band_width": round(max(0.0, feasible_upper - bound), 4),
            })
    return bands


def spearman(first, second):
    first_ranks = first.argsort().argsort()
    second_ranks = second.argsort().argsort()
    return float(np.corrcoef(first_ranks, second_ranks)[0, 1])


def aggregation_rule_comparison(layers):
    """Table 3: ADMI versus compensatory, symmetric-penalty and fully non-compensatory aggregation rules."""
    base_index, final_index = admi(layers, **CALIBRATED_PARAMETERS)
    mazziotta_pareto_index = mazziotta_pareto(layers)
    rules = {
        "arithmetic_mean": base_index,
        "adma_penalised": final_index,
        "mazziotta_pareto": mazziotta_pareto_index,
        "geometric_mean": np.exp(np.log(np.maximum(layers, 1e-9)).mean(axis=1)),
        "minimum": layers.min(axis=1),
    }
    spread = layers.max(axis=1) - layers.min(axis=1)
    summary = {}
    for rule_name, values in rules.items():
        levels = maturity_level(values)
        summary[rule_name] = {
            "mean": round(float(values.mean()), 4),
            "spearman_with_mean": round(spearman(values, base_index), 4),
            "spearman_with_minimum": round(spearman(values, rules["minimum"]), 4),
            "level_distribution": {str(level): round(float((levels == level).mean()), 4) for level in range(1, 6)},
            "correlation_of_adjustment_with_profile_spread":
                round(float(np.corrcoef(values - base_index, spread)[0, 1]), 4) if rule_name != "arithmetic_mean" else None,
        }
    # Asymmetry: the strongest layer exceeds the median of the profile by more than 0.25 and no layer is below
    # the threshold delta. ADMI does not lower such profiles, the Mazziotta-Pareto index does.
    leading_layer = ((layers.max(axis=1) - np.median(layers, axis=1) > 0.25)
                     & (layers.min(axis=1) >= CALIBRATED_PARAMETERS["delta"]))
    summary["asymmetry_check"] = {
        "share_profiles_with_leading_layer_and_no_weak_layer": round(float(leading_layer.mean()), 4),
        "mean_mazziotta_pareto_reduction_on_them": round(float((base_index - mazziotta_pareto_index)[leading_layer].mean()), 4),
        "mean_adma_reduction_on_them": round(float((base_index - final_index)[leading_layer].mean()), 4),
    }
    return summary


def integration_masking(layers, integration):
    """P2: scalar with DM_I as a sixth component versus the pair (ADMI, DM_I)."""
    _, final_index = admi(layers, **CALIBRATED_PARAMETERS)
    scalar_with_integration = np.column_stack([layers, integration]).mean(axis=1)
    scalar_level = maturity_level(scalar_with_integration)
    final_level = maturity_level(final_index)
    illusion = (final_level >= 3) & (integration <= 0.20)  # "illusion of maturity"
    illusion_kept_by_scalar = illusion & (scalar_level >= 3)
    # A stronger alternative: DM_I as a sixth layer of the penalised index (same alpha and delta).
    _, six_layer_index = admi(np.column_stack([layers, integration]), **CALIBRATED_PARAMETERS)
    illusion_kept_by_six_layer_admi = illusion & (maturity_level(six_layer_index) >= 3)
    generator = np.random.default_rng(SEED + 1)
    first = generator.integers(0, len(layers), 200_000)
    second = generator.integers(0, len(layers), 200_000)
    same_scalar_level = scalar_level[first] == scalar_level[second]
    large_integration_gap = np.abs(integration[first] - integration[second]) >= 0.50
    return {
        "share_illusion_of_maturity": round(float(illusion.mean()), 4),
        "share_of_illusions_kept_at_level_3plus_by_scalar": round(float(illusion_kept_by_scalar.sum() / max(illusion.sum(), 1)), 4),
        "share_of_illusions_kept_at_level_3plus_by_six_layer_admi": round(float(illusion_kept_by_six_layer_admi.sum() / max(illusion.sum(), 1)), 4),
        "share_same_scalar_level_pairs_with_integration_gap_ge_0_50": round(float(large_integration_gap[same_scalar_level].mean()), 4),
    }


def sensitivity(layers):
    """P3: agreement of levels with the calibrated parameters over a 9 x 11 grid of alpha and delta.

    Agreement over all profiles is high partly because the penalty never changes the level of most profiles,
    so two further measures are reported: the agreement of the unpenalised mean (baseline) and the agreement
    on sensitive profiles, i.e. profiles whose level differs from the unpenalised level for at least one grid cell.
    """
    base_index, reference_index = admi(layers, **CALIBRATED_PARAMETERS)
    reference_level = maturity_level(reference_index)
    base_level = maturity_level(base_index)
    cells = [(float(alpha), float(delta)) for alpha in np.round(np.arange(0.30, 0.701, 0.05), 2)
             for delta in np.round(np.arange(0.15, 0.401, 0.025), 3)]
    levels = {cell: maturity_level(admi(layers, *cell)[1]) for cell in cells}
    sensitive = np.zeros(len(layers), dtype=bool)
    for cell_levels in levels.values():
        sensitive |= cell_levels != base_level
    grid = []
    for alpha, delta in cells:
        cell_levels = levels[(alpha, delta)]
        grid.append({
            "alpha": alpha,
            "delta": delta,
            "agreement_with_calibrated": round(float((cell_levels == reference_level).mean()), 4),
            "agreement_with_calibrated_sensitive_profiles": round(float((cell_levels == reference_level)[sensitive].mean()), 4),
            "share_level_changed_vs_base": round(float((cell_levels != base_level).mean()), 4),
        })

    def zone(key, alpha_range, delta_range):
        return [cell[key] for cell in grid if alpha_range[0] - 1e-9 <= cell["alpha"] <= alpha_range[1] + 1e-9
                and delta_range[0] - 1e-9 <= cell["delta"] <= delta_range[1] + 1e-9]

    agreements = [cell["agreement_with_calibrated"] for cell in grid]
    sensitive_agreements = [cell["agreement_with_calibrated_sensitive_profiles"] for cell in grid]
    optimum_zone = zone("agreement_with_calibrated", (0.35, 0.50), (0.35, 0.40))
    worst_sensitive = min(grid, key=lambda cell: cell["agreement_with_calibrated_sensitive_profiles"])
    return {
        "min_agreement": min(agreements),
        "mean_agreement": round(float(np.mean(agreements)), 4),
        "near_calibrated_min_agreement": min(zone("agreement_with_calibrated", (0.35, 0.45), (0.325, 0.40))),
        "calibration_optimum_zone_min_agreement": min(optimum_zone),
        "calibration_optimum_zone_mean_agreement": round(float(np.mean(optimum_zone)), 4),
        "baseline_no_penalty_agreement": round(float((base_level == reference_level).mean()), 4),
        "share_sensitive_profiles": round(float(sensitive.mean()), 4),
        "sensitive_min_agreement": min(sensitive_agreements),
        "sensitive_min_agreement_cell": {"alpha": worst_sensitive["alpha"], "delta": worst_sensitive["delta"]},
        "sensitive_mean_agreement": round(float(np.mean(sensitive_agreements)), 4),
        "sensitive_near_calibrated_min_agreement": min(zone("agreement_with_calibrated_sensitive_profiles", (0.35, 0.45), (0.325, 0.40))),
        "sensitive_baseline_no_penalty_agreement": round(float((base_level == reference_level)[sensitive].mean()), 4),
        "grid": grid,
    }


def worked_example():
    """Worked example at the start of Section 4: a profile reachable by real answers in which the penalty changes the level."""
    profile = {"C": 7 / 12, "L1": 0.50, "L2": 0.50, "L3": 1 / 12, "L4": 0.50}
    layers = np.array([list(profile.values())])
    base_index, final_index = admi(layers, **CALIBRATED_PARAMETERS)
    return {
        "profile": {name: round(value, 4) for name, value in profile.items()},
        "base_index": round(float(base_index[0]), 4),
        "penalty": round(float(penalty(layers.min(), **CALIBRATED_PARAMETERS)), 4),
        "final_index": round(float(final_index[0]), 4),
        "base_level": int(maturity_level(base_index)[0]),
        "final_level": int(maturity_level(final_index)[0]),
    }


def diagnostic_situations():
    """Table 4: diagnostic situations on illustrative profiles."""
    situations = {
        "compliance_trap": ({"C": 0.70, "L1": 0.40, "L2": 0.45, "L3": 0.05, "L4": 0.60}, 0.30, 0.40),
        "external_eu_pressure": ({"C": 0.35, "L1": 0.30, "L2": 0.35, "L3": 0.30, "L4": 0.70}, 0.15, 0.30),
        "absorptive_limiter": ({"C": 0.55, "L1": 0.10, "L2": 0.45, "L3": 0.45, "L4": 0.50}, 0.35, 0.40),
        "aware_mismatch": ({"C": 0.30, "L1": 0.25, "L2": 0.25, "L3": 0.30, "L4": 0.25}, 0.20, 0.75),
        "illusion_of_maturity": ({"C": 0.55, "L1": 0.55, "L2": 0.55, "L3": 0.55, "L4": 0.55}, 0.15, 0.50),
    }
    results = {}
    for name, (profile, integration, strategy) in situations.items():
        layers = np.array([list(profile.values())])
        base_index, final_index = admi(layers, **CALIBRATED_PARAMETERS)
        scalar = float(np.append(layers, integration).mean())
        results[name] = {
            "profile": profile, "DM_I": integration, "DM_S": strategy,
            "base_index": round(float(base_index[0]), 4),
            "final_index": round(float(final_index[0]), 4),
            "level": int(maturity_level(final_index)[0]),
            "scalar_with_DM_I": round(scalar, 4),
            "scalar_level": int(maturity_level(np.array([scalar]))[0]),
        }
    return results


def main():
    profiles_by_scenario = {scenario_name: load_profiles(scenario_name) for scenario_name in RESPONSE_SCENARIOS}
    report = {
        "meta": {
            "profiles": "data/generated/profiles_<scenario>.csv, generated with seed %d" % SEED,
            "profile_count_per_scenario": len(profiles_by_scenario["uniform"]["layers"]),
            "python": platform.python_version(), "numpy": np.__version__,
            "calibrated_parameters": CALIBRATED_PARAMETERS, "initial_parameters": INITIAL_PARAMETERS,
            "theoretical_bounds": THEORETICAL_BOUNDS, "model_adjusted_bounds": MODEL_ADJUSTED_BOUNDS,
        },
        "worked_example": worked_example(),
        "diagnostic_situations": diagnostic_situations(),
        "boundary_band_calibrated": boundary_band(**CALIBRATED_PARAMETERS),
        "scenarios": {},
    }
    for scenario_name, profiles in profiles_by_scenario.items():
        layers = profiles["layers"]
        report["scenarios"][scenario_name] = {
            "P1_calibrated": level_change_summary(layers, **CALIBRATED_PARAMETERS),
            "P1_initial": level_change_summary(layers, **INITIAL_PARAMETERS),
            "P1_calibrated_model_adjusted_bounds": level_change_summary(layers, bounds=MODEL_ADJUSTED_BOUNDS, **CALIBRATED_PARAMETERS),
            "P1_residual_masking": residual_masking(layers, **CALIBRATED_PARAMETERS),
            "aggregation_rules": aggregation_rule_comparison(layers),
            "P2_integration_masking": integration_masking(layers, profiles["integration"]),
            "P3_sensitivity": sensitivity(layers),
        }
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")

    example = report["worked_example"]
    print("Worked example: ADMI_base %.3f (level %d) -> penalty %.3f -> ADMI %.3f (level %d)" % (
        example["base_index"], example["base_level"], example["penalty"], example["final_index"], example["final_level"]))
    for scenario_name, scenario in report["scenarios"].items():
        p1 = scenario["P1_calibrated"]
        p2 = scenario["P2_integration_masking"]
        p3 = scenario["P3_sensitivity"]
        print("[%s] P1: penalised %.1f%%, level changed %.1f%% | P2: illusions %.1f%%, kept at 3+ by scalar %.1f%% | "
              "P3: min agreement %.1f%%, mean %.1f%%" % (
                  scenario_name, 100 * p1["share_penalised"], 100 * p1["share_level_changed"],
                  100 * p2["share_illusion_of_maturity"], 100 * p2["share_of_illusions_kept_at_level_3plus_by_scalar"],
                  100 * p3["min_agreement"], 100 * p3["mean_agreement"]))
    print("Saved:", RESULTS_PATH)


if __name__ == "__main__":
    main()
