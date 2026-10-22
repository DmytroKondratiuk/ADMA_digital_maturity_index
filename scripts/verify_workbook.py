"""Check that the Excel formulas of excel/ADMA_workbook.xlsx give the same numbers as the Python scripts.

The workbook formulas are evaluated with pycel (an independent Excel formula engine), and every
result is compared with the Python implementation:
  Calculator and Worked_example, Statistics_mode (Table 7), Diagnostic_situations (Table 6),
  Boundary_band (equation 7) and all rows of Experiment_sample.

Usage:  python scripts/verify_workbook.py     (requires openpyxl and pycel)
Exit code 0 if every value agrees within 1e-9, 1 otherwise.
"""

import sys
from pathlib import Path

import numpy as np
from openpyxl import load_workbook
from openpyxl.workbook.defined_name import DefinedNameDict
from pycel import ExcelCompiler

# pycel 1.0b30 reads defined names through the pre-3.1 openpyxl attribute `definedName`.
if not hasattr(DefinedNameDict, "definedName"):
    DefinedNameDict.definedName = property(lambda names: list(names.values()))

sys.path.insert(0, str(Path(__file__).resolve().parent))

from adma_index import CALIBRATED_PARAMETERS, ITEMS_PER_LAYER, admi, maturity_level, penalty  # noqa: E402
from build_workbook import OUTPUT_PATH, SAMPLE_SIZE, WORKED_EXAMPLE_ANSWERS  # noqa: E402
from data_sources import RAW_DATA  # noqa: E402
from generate_profiles import GENERATED_DATA, column_names  # noqa: E402
from simulation_experiment import boundary_band, diagnostic_situations  # noqa: E402
from statistics_mode_local import compute_statistics_mode  # noqa: E402

TOLERANCE = 1e-9


class Checker:
    def __init__(self):
        self.checked = 0
        self.failures = []

    def equal(self, label, excel_value, python_value):
        self.checked += 1
        if isinstance(python_value, str) or isinstance(excel_value, str):
            agrees = str(excel_value) == str(python_value)
        else:
            agrees = excel_value is not None and abs(float(excel_value) - float(python_value)) <= TOLERANCE
        if not agrees:
            self.failures.append("%s: Excel %r, Python %r" % (label, excel_value, python_value))


def find_row(sheet, column, label):
    for row in range(1, sheet.max_row + 1):
        if sheet.cell(row=row, column=column).value == label:
            return row
    raise KeyError(label)


def check_calculator(compiler, formulas, checker, sheet_name):
    sheet = formulas[sheet_name]
    answers = np.array(WORKED_EXAMPLE_ANSWERS)
    normalised = (answers - 1) / 4
    starts = {}
    position = 0
    for block, count in list(ITEMS_PER_LAYER.items()) + [("I", 3), ("S", 2)]:
        starts[block] = (position, count)
        position += count
    layers = np.array([normalised[start:start + count].mean() for block, (start, count) in starts.items() if block in ITEMS_PER_LAYER])
    base_index, final_index = admi(layers, **CALIBRATED_PARAMETERS)
    expected = {
        "ADMI_base (eq. 3)": base_index[0],
        "DM_min": layers.min(),
        "Penalty P (eq. 4)": float(penalty(layers.min(), **CALIBRATED_PARAMETERS)),
        "ADMI (eq. 5)": final_index[0],
        "Level by ADMI_base": int(maturity_level(base_index)[0]),
        "Level by ADMI": int(maturity_level(final_index)[0]),
        "DM_I (integration, outside the index)": normalised[starts["I"][0]:starts["I"][0] + 3].mean(),
        "DM_S (strategy, outside the index)": normalised[starts["S"][0]:starts["S"][0] + 2].mean(),
    }
    for layer, value in zip(ITEMS_PER_LAYER, layers):
        expected["DM_%s (eq. 2)" % layer] = value
    for label, value in expected.items():
        row = find_row(sheet, 3, label)
        checker.equal("%s/%s" % (sheet_name, label), compiler.evaluate("%s!D%d" % (sheet_name, row)), value)


def check_statistics_mode(compiler, checker):
    result = compute_statistics_mode(RAW_DATA)
    for offset, row in enumerate(result["rows"]):
        excel_row = 4 + offset
        checker.equal("Table7/%s/Ukraine" % row["name"], compiler.evaluate("Statistics_mode!D%d" % excel_row), row["ukraine_percent"])
        checker.equal("Table7/%s/EU27" % row["name"], compiler.evaluate("Statistics_mode!F%d" % excel_row), row["eu27_percent"])
        checker.equal("Table7/%s/leader" % row["name"], compiler.evaluate("Statistics_mode!H%d" % excel_row), row["leader_country"])
        checker.equal("Table7/%s/leader value" % row["name"], compiler.evaluate("Statistics_mode!I%d" % excel_row), row["leader_percent"])
        checker.equal("Table7/%s/DM Ukraine" % row["name"], round(compiler.evaluate("Statistics_mode!J%d" % excel_row), 3), row["ukraine_score"])
        checker.equal("Table7/%s/DM EU27" % row["name"], round(compiler.evaluate("Statistics_mode!K%d" % excel_row), 3), row["eu27_score"])
    profile_start = 4 + len(result["rows"]) + 3
    for offset, (layer, scores) in enumerate(result["layer_profile"].items()):
        excel_row = profile_start + offset
        checker.equal("Table7/profile %s/Ukraine" % layer, round(compiler.evaluate("Statistics_mode!B%d" % excel_row), 3), scores["ukraine"])
        checker.equal("Table7/profile %s/EU27" % layer, round(compiler.evaluate("Statistics_mode!C%d" % excel_row), 3), scores["eu27"])


def check_diagnostic_situations(compiler, checker):
    for offset, (name, expected) in enumerate(diagnostic_situations().items()):
        row = 4 + offset
        checker.equal("Table6/%s/base" % name, round(compiler.evaluate("Diagnostic_situations!I%d" % row), 4), expected["base_index"])
        checker.equal("Table6/%s/ADMI" % name, round(compiler.evaluate("Diagnostic_situations!L%d" % row), 4), expected["final_index"])
        checker.equal("Table6/%s/level" % name, compiler.evaluate("Diagnostic_situations!M%d" % row), expected["level"])
        checker.equal("Table6/%s/scalar" % name, round(compiler.evaluate("Diagnostic_situations!N%d" % row), 4), expected["scalar_with_DM_I"])
        checker.equal("Table6/%s/scalar level" % name, compiler.evaluate("Diagnostic_situations!O%d" % row), expected["scalar_level"])


def check_boundary_band(compiler, checker):
    for offset, expected in enumerate(boundary_band(**CALIBRATED_PARAMETERS)):
        row = 4 + offset
        checker.equal("Band/b=%s,DMmin=%s/width" % (expected["bound"], expected["layer_minimum"]),
                      round(compiler.evaluate("Boundary_band!F%d" % row), 4), expected["band_width"])


def check_experiment_sample(compiler, formulas, checker):
    sheet = formulas["Experiment_sample"]
    header_row = 8
    headers = {sheet.cell(row=header_row, column=column).value: sheet.cell(row=header_row, column=column).column_letter
               for column in range(1, sheet.max_column + 1)}
    responses = np.loadtxt(str(GENERATED_DATA / "profiles_uniform.csv"), delimiter=",", skiprows=1, dtype=np.int64, max_rows=SAMPLE_SIZE)[:, 1:]
    names = column_names()

    def block(prefix, count):
        start = names.index("%s_1" % prefix)
        return ((responses[:, start:start + count] - 1) / 4).mean(axis=1)

    layers = np.column_stack([block(layer, count) for layer, count in ITEMS_PER_LAYER.items()])
    integration = block("I", 3)
    base_index, final_index = admi(layers, **CALIBRATED_PARAMETERS)
    base_level = maturity_level(base_index)
    final_level = maturity_level(final_index)
    scalar = np.column_stack([layers, integration]).mean(axis=1)
    expected_columns = {
        "ADMI_base": base_index, "ADMI": final_index, "Level base": base_level, "Level ADMI": final_level,
        "Level changed": (base_level != final_level).astype(int),
        "Illusion of maturity": ((final_level >= 3) & (integration <= 0.20)).astype(int),
        "Scalar level": maturity_level(scalar),
    }
    for offset in range(SAMPLE_SIZE):
        row = header_row + 1 + offset
        for header, values in expected_columns.items():
            checker.equal("Sample/row %d/%s" % (offset + 1, header), compiler.evaluate("Experiment_sample!%s%d" % (headers[header], row)), values[offset])


def main():
    if not OUTPUT_PATH.exists():
        sys.exit("Workbook not found; run scripts/build_workbook.py first.")
    compiler = ExcelCompiler(filename=str(OUTPUT_PATH))
    formulas = load_workbook(str(OUTPUT_PATH))
    checker = Checker()
    check_calculator(compiler, formulas, checker, "Calculator")
    check_calculator(compiler, formulas, checker, "Worked_example")
    check_statistics_mode(compiler, checker)
    check_diagnostic_situations(compiler, checker)
    check_boundary_band(compiler, checker)
    check_experiment_sample(compiler, formulas, checker)
    print("Checked %d values." % checker.checked)
    if checker.failures:
        print("%d disagreements:" % len(checker.failures))
        for failure in checker.failures[:50]:
            print("  " + failure)
        sys.exit(1)
    print("All Excel formulas agree with the Python scripts.")


if __name__ == "__main__":
    main()
