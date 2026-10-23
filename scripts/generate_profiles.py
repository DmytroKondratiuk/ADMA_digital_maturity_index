"""Generate the synthetic questionnaire responses used in the computational experiment.

Writes one CSV per response scenario to data/generated/. Each row is one simulated enterprise
with 21 Likert answers (1..5) in questionnaire order:
  C_1..C_3, L1_1..L1_3, L2_1..L2_3, L3_1..L3_3, L4_1..L4_3 (operational layers),
  I_1..I_3 (integration, DM_I), S_1..S_3 (strategy, DM_S).

The files are part of the repository, so this script only needs to be run to regenerate them.
The generator is seeded; regenerating gives byte-identical files.

Usage:  python scripts/generate_profiles.py
"""

import csv
import io
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from adma_index import ITEMS_INTEGRATION, ITEMS_PER_LAYER, ITEMS_STRATEGY  # noqa: E402

SEED = 2026
PROFILE_COUNT = 100_000
RESPONSE_SCENARIOS = {
    "uniform": [0.2, 0.2, 0.2, 0.2, 0.2],  # whole response space
    "low_skewed": [0.30, 0.30, 0.20, 0.13, 0.07],  # robustness check, mostly low scores
}
GENERATED_DATA = Path(__file__).resolve().parent.parent / "data" / "generated"


def column_names():
    names = []
    for layer, item_count in ITEMS_PER_LAYER.items():
        names.extend("%s_%d" % (layer, number) for number in range(1, item_count + 1))
    names.extend("I_%d" % number for number in range(1, ITEMS_INTEGRATION + 1))
    names.extend("S_%d" % number for number in range(1, ITEMS_STRATEGY + 1))
    return names


def generate(generator, profile_count, response_probabilities):
    """Answers are drawn block by block in questionnaire order (layers, then I, then S)."""
    blocks = [generator.choice(np.arange(1, 6), size=(profile_count, item_count), p=response_probabilities)
              for item_count in ITEMS_PER_LAYER.values()]
    blocks.append(generator.choice(np.arange(1, 6), size=(profile_count, ITEMS_INTEGRATION), p=response_probabilities))
    blocks.append(generator.choice(np.arange(1, 6), size=(profile_count, ITEMS_STRATEGY), p=response_probabilities))
    return np.column_stack(blocks)


def main():
    generator = np.random.default_rng(SEED)
    GENERATED_DATA.mkdir(parents=True, exist_ok=True)
    for scenario_name, response_probabilities in RESPONSE_SCENARIOS.items():
        responses = generate(generator, PROFILE_COUNT, response_probabilities)
        path = GENERATED_DATA / ("profiles_%s.csv" % scenario_name)
        with io.open(str(path), "w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["profile_id"] + column_names())
            for profile_id, row in enumerate(responses, start=1):
                writer.writerow([profile_id] + row.tolist())
        print("Saved:", path, responses.shape)


if __name__ == "__main__":
    main()
