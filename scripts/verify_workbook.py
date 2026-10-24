"""Check that the Excel formulas of excel/ADMA_workbook.xlsx and excel/ADMA_workbook_ua.xlsx give the same numbers
as the Python scripts.

The workbook formulas are evaluated with pycel (an independent Excel formula engine), and every
result is compared with the Python implementation:
  Calculator and Worked_example, Statistics_mode (Tables 5 and 6), TOPSIS, Diagnostic_situations (Table 4),
  Boundary_band (equation 7) and all rows of Experiment_sample.

Usage:  python scripts/verify_workbook.py     (requires openpyxl and pycel)
Exit code 0 if every value of both workbooks agrees within 1e-9, 1 otherwise.
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

from adma_index import CALIBRATED_PARAMETERS, ITEMS_INTEGRATION, ITEMS_PER_LAYER, ITEMS_STRATEGY, admi, maturity_level, penalty  # noqa: E402
from build_workbook import (  # noqa: E402
    SAMPLE_SIZE, STATISTICS_FIRST_ROW, STATISTICS_INDICATORS, TOPSIS_FIRST_ROW, WORKBOOKS, WORKED_EXAMPLE_ANSWERS, index_cell, ref,
    sample_label, set_language, sheet_name, tr)
from data_sources import read_matrix  # noqa: E402
from generate_profiles import GENERATED_DATA, column_names  # noqa: E402
from simulation_experiment import boundary_band, diagnostic_situations  # noqa: E402
from statistics_mode_local import RANKED, TABLE_ROWS, compute_statistics_mode  # noqa: E402

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


def check_calculator(compiler, formulas, checker, name):
    sheet = formulas[sheet_name(name)]
    answers = np.array(WORKED_EXAMPLE_ANSWERS)
    normalised = (answers - 1) / 4
    starts = {}
    position = 0
    for block, count in list(ITEMS_PER_LAYER.items()) + [("I", ITEMS_INTEGRATION), ("S", ITEMS_STRATEGY)]:
        starts[block] = (position, count)
        position += count
    layers = np.array([normalised[start:start + count].mean() for block, (start, count) in starts.items() if block in ITEMS_PER_LAYER])
    base_index, final_index = admi(layers, **CALIBRATED_PARAMETERS)
    expected = {
        tr("ADMI_base (eq. 3)"): base_index[0],
        "DM_min": layers.min(),
        tr("Penalty P (eq. 4)"): float(penalty(layers.min(), **CALIBRATED_PARAMETERS)),
        tr("ADMI (eq. 5)"): final_index[0],
        tr("Level by ADMI_base"): int(maturity_level(base_index)[0]),
        tr("Level by ADMI"): int(maturity_level(final_index)[0]),
        tr("DM_I (integration, outside the index)"): normalised[starts["I"][0]:starts["I"][0] + ITEMS_INTEGRATION].mean(),
        tr("DM_S (strategy, outside the index)"): normalised[starts["S"][0]:starts["S"][0] + ITEMS_STRATEGY].mean(),
    }
    for layer, value in zip(ITEMS_PER_LAYER, layers):
        expected[tr("DM_%s (eq. 2)") % layer] = value
    for label, value in expected.items():
        row = find_row(sheet, 3, label)
        checker.equal("%s/%s" % (name, label), compiler.evaluate("%sD%d" % (ref(name), row)), value)


def check_statistics_mode(compiler, checker):
    """Tables 5 and 6: leaders, indicator scores, layers, ADMI, levels and ranks; TOPSIS weights, closeness, ranks, Spearman."""
    matrix = {row["pair_id"]: row for row in read_matrix()}
    result = compute_statistics_mode(list(matrix.values()))
    for offset, code in enumerate(STATISTICS_INDICATORS):
        row = STATISTICS_FIRST_ROW + offset
        checker.equal("Table5/%s/leader" % code, compiler.evaluate(ref("Statistics_mode") + "G%d" % row), matrix[code]["leader_country"])
        checker.equal("Table5/%s/leader value" % code, compiler.evaluate(ref("Statistics_mode") + "H%d" % row), result["years_and_leaders"][code]["leader_value"])
        for country_offset, country in enumerate(TABLE_ROWS):
            expected = result["indicator_scores"][code][country]
            excel_value = compiler.evaluate("%s%s%d" % (ref("Statistics_mode"), _letter(9 + country_offset), row))
            if expected is None:
                checker.equal("Table5/%s/%s" % (code, country), excel_value, "")
            else:
                checker.equal("Table5/%s/%s" % (code, country), excel_value, expected)
    for country in TABLE_ROWS:
        expected = result["countries"][country]
        values = dict(expected["layers"], ADMI_base=expected["ADMI_base"], DM_min=expected["DM_min"], Penalty=expected["penalty"],
                      ADMI=expected["ADMI"], Level=expected["level"], DM_I=expected["DM_I"], DM_S=expected["DM_S"])
        if country in RANKED:
            values["Rank ADMI"] = result["ranking"][country]["ADMI_rank"]
            values["Rank TOPSIS"] = result["ranking"][country]["TOPSIS_rank"]
        for header, value in values.items():
            checker.equal("Table5/%s/%s" % (country, header), compiler.evaluate(ref("Statistics_mode") + index_cell(country, header)), value)
    for offset, country in enumerate(RANKED):
        row = TOPSIS_FIRST_ROW + offset
        checker.equal("TOPSIS/%s/closeness" % country, compiler.evaluate(ref("TOPSIS") + "AB%d" % row), result["ranking"][country]["TOPSIS_closeness"])
    weight_row = TOPSIS_FIRST_ROW + len(RANKED) - 1 + 4
    for layer_offset, (layer, weight) in enumerate(result["entropy_weights"].items()):
        checker.equal("TOPSIS/weight %s" % layer, compiler.evaluate("%s%s%d" % (ref("TOPSIS"), _letter(2 + layer_offset), weight_row)), weight)
    spearman_row = TOPSIS_FIRST_ROW + len(RANKED) - 1 + 8
    checker.equal("TOPSIS/Spearman", compiler.evaluate(ref("TOPSIS") + "B%d" % spearman_row), result["spearman_ADMI_TOPSIS"])


def _letter(column):
    from openpyxl.utils import get_column_letter
    return get_column_letter(column)


def check_diagnostic_situations(compiler, checker):
    for offset, (name, expected) in enumerate(diagnostic_situations().items()):
        row = 4 + offset
        checker.equal("Table4/%s/base" % name, round(compiler.evaluate(ref("Diagnostic_situations") + "I%d" % row), 4), expected["base_index"])
        checker.equal("Table4/%s/ADMI" % name, round(compiler.evaluate(ref("Diagnostic_situations") + "L%d" % row), 4), expected["final_index"])
        checker.equal("Table4/%s/level" % name, compiler.evaluate(ref("Diagnostic_situations") + "M%d" % row), expected["level"])
        checker.equal("Table4/%s/scalar" % name, round(compiler.evaluate(ref("Diagnostic_situations") + "N%d" % row), 4), expected["scalar_with_DM_I"])
        checker.equal("Table4/%s/scalar level" % name, compiler.evaluate(ref("Diagnostic_situations") + "O%d" % row), expected["scalar_level"])


def check_boundary_band(compiler, checker):
    for offset, expected in enumerate(boundary_band(**CALIBRATED_PARAMETERS)):
        row = 4 + offset
        checker.equal("Band/b=%s,DMmin=%s/width" % (expected["bound"], expected["layer_minimum"]),
                      round(compiler.evaluate(ref("Boundary_band") + "F%d" % row), 4), expected["band_width"])


def check_experiment_sample(compiler, formulas, checker):
    sheet = formulas[sheet_name("Experiment_sample")]
    header_row = 8
    headers = {sheet.cell(row=header_row, column=column).value: sheet.cell(row=header_row, column=column).column_letter
               for column in range(1, sheet.max_column + 1)}
    responses = np.loadtxt(str(GENERATED_DATA / "profiles_uniform.csv"), delimiter=",", skiprows=1, dtype=np.int64, max_rows=SAMPLE_SIZE)[:, 1:]
    names = column_names()

    def block(prefix, count):
        start = names.index("%s_1" % prefix)
        return ((responses[:, start:start + count] - 1) / 4).mean(axis=1)

    layers = np.column_stack([block(layer, count) for layer, count in ITEMS_PER_LAYER.items()])
    integration = block("I", ITEMS_INTEGRATION)
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
            checker.equal("Sample/row %d/%s" % (offset + 1, header), compiler.evaluate("%s%s%d" % (ref("Experiment_sample"), headers[sample_label(header)], row)), values[offset])


def verify(code):
    """Number of disagreements in the workbook of one language."""
    set_language(code)
    path = WORKBOOKS[code][0]
    if not path.exists():
        sys.exit("Workbook %s not found; run scripts/build_workbook.py first." % path.name)
    compiler = ExcelCompiler(filename=str(path))
    formulas = load_workbook(str(path))
    checker = Checker()
    check_calculator(compiler, formulas, checker, "Calculator")
    check_calculator(compiler, formulas, checker, "Worked_example")
    check_statistics_mode(compiler, checker)
    check_diagnostic_situations(compiler, checker)
    check_boundary_band(compiler, checker)
    check_experiment_sample(compiler, formulas, checker)
    print("%s: checked %d values." % (path.name, checker.checked))
    if checker.failures:
        print("%d disagreements:" % len(checker.failures))
        for failure in checker.failures[:50]:
            print("  " + failure)
    return len(checker.failures)


def main():
    if sum(verify(code) for code in WORKBOOKS):
        sys.exit(1)
    print("All Excel formulas agree with the Python scripts.")


if __name__ == "__main__":
    main()
