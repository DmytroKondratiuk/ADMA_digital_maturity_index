"""Core formulas of the ADMA digital maturity assessment.

Equation numbers follow the paper:
  (1) item normalisation, (2) layer score, (3) base index, (4) weak-link penalty,
  (5) final ADMI, (6) min-max normalisation of the statistics mode.
"""

import numpy as np

# Number of questionnaire statements per block.
ITEMS_PER_LAYER = {"C": 3, "L1": 2, "L2": 3, "L3": 3, "L4": 3}  # operational layers, enter the index
ITEMS_INTEGRATION = 3  # DM_I, kept outside the index
ITEMS_STRATEGY = 2  # DM_S, kept outside the index
LAYERS = list(ITEMS_PER_LAYER)

CALIBRATED_PARAMETERS = {"alpha": 0.40, "delta": 0.375}  # calibrated on the IM Onion-S simulation model
INITIAL_PARAMETERS = {"alpha": 0.50, "delta": 0.25}  # initial hypothesis justified by the scale

THEORETICAL_BOUNDS = (0.20, 0.40, 0.60, 0.80)  # Table 2 of the paper
MODEL_ADJUSTED_BOUNDS = (0.25, 0.45, 0.60, 0.80)  # used only as a robustness check of H1


def normalise_item(score):
    """Equation (1): Likert score 1..5 -> [0, 1]."""
    return (np.asarray(score, dtype=float) - 1.0) / 4.0


def layer_score(item_scores):
    """Equation (2): mean of normalised item scores along the last axis."""
    return normalise_item(item_scores).mean(axis=-1)


def penalty(layer_minimum, alpha, delta):
    """Equation (4): weak-link penalty."""
    return 1.0 - alpha * np.maximum(0.0, delta - np.asarray(layer_minimum, dtype=float))


def admi(layers, alpha, delta):
    """Equations (3) and (5). `layers` has shape (profiles, 5). Returns (base index, final index)."""
    layers = np.atleast_2d(layers)
    base_index = layers.mean(axis=1)
    final_index = base_index * penalty(layers.min(axis=1), alpha, delta)
    return base_index, final_index


CLASSIFICATION_DECIMALS = 12  # removes floating-point noise so that exact ties with a bound are detected


def maturity_level(index_values, bounds=THEORETICAL_BOUNDS):
    """Level 1..5. A value exactly on a bound belongs to the lower level (0.40 -> level 2).

    Index values are multiples of 1/120 for questionnaire answers, so exact ties with a bound occur;
    rounding to 12 decimals makes the tie test independent of the order of floating-point operations
    (the Excel workbook applies the same rounding).
    """
    rounded = np.round(np.asarray(index_values, dtype=float), CLASSIFICATION_DECIMALS)
    return np.searchsorted(np.asarray(bounds), rounded, side="left") + 1


def statistics_mode_score(value, leader_value, minimum_value=0.0):
    """Equation (6) with P_min = minimum_value (0 when no regional data exist)."""
    return (value - minimum_value) / (leader_value - minimum_value)
