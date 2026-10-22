"""Build excel/ADMA_workbook.xlsx: every calculation of the paper that can be checked by hand,
written as live Excel formulas (not pasted values).

Sheets: README, Parameters, Calculator, Statistics_mode (Table 7), EU_data, UA_data,
Diagnostic_situations (Table 6), Worked_example (Section 4.1), Boundary_band (equation 7),
Experiment_sample (first 1 000 profiles of the uniform scenario).

Inputs are read from data/raw/, data/generated/ and results/simulation_experiment.json, so the workbook
always matches the scripts. excel/README.md is written from the same text as the README sheet.
Run scripts/simulation_experiment.py first.

Usage:  python scripts/build_workbook.py     (requires openpyxl)
"""

import csv
import io
import json
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation

sys.path.insert(0, str(Path(__file__).resolve().parent))

from adma_index import CALIBRATED_PARAMETERS, ITEMS_PER_LAYER, THEORETICAL_BOUNDS  # noqa: E402
from data_sources import (  # noqa: E402
    EU27_COUNTRIES, RAW_DATA, REPOSITORY_ROOT, STATISTICS_MODE_INDICATORS, eurostat_url, eurostat_values, read_csv,
    ukrstat_url, ukrstat_value)
from generate_profiles import GENERATED_DATA, column_names  # noqa: E402

OUTPUT_PATH = REPOSITORY_ROOT / "excel" / "ADMA_workbook.xlsx"
README_PATH = REPOSITORY_ROOT / "excel" / "README.md"
SIMULATION_RESULTS = REPOSITORY_ROOT / "results" / "simulation_experiment.json"
SAMPLE_SIZE = 1000

BOLD = Font(bold=True)
TITLE = Font(bold=True, size=13)
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")  # yellow: values a reviewer may change
SOURCE_FILL = PatternFill("solid", fgColor="DDEBF7")  # blue: values copied from official sources
WRAP = Alignment(wrap_text=True, vertical="top")

STATEMENTS = [
    ("C", "Software for production and resource planning (ERP, MES)"),
    ("C", "Automation of production processes with digital equipment"),
    ("C", "Approved digital development strategy or plan for 2-3 years"),
    ("L1", "Digital tools for human resource management (HRM)"),
    ("L1", "Employees have the skills to work with digital tools"),
    ("L2", "Digital accounting of inventories (WMS or spreadsheets)"),
    ("L2", "Collection and analysis of data on resource use, deviations and losses"),
    ("L2", "Monitoring of storage conditions with sensors or IoT"),
    ("L3", "GPS monitoring or telematics on vehicles and machinery"),
    ("L3", "Data-based maintenance planning (CMMS)"),
    ("L3", "Precision farming or precision livestock technologies"),
    ("L4", "Digital sales channels (website, e-commerce, EDI)"),
    ("L4", "Systematic collection and analysis of demand, price and feedback data (CRM)"),
    ("L4", "Digital traceability: verified information on product origin"),
    ("I", "Automatic transfer of production data between units"),
    ("I", "Timely receipt of external data (prices, weather, regulation)"),
    ("I", "Integration of the enterprise's digital systems with each other"),
    ("S", "Regular tracking of new digital technologies"),
    ("S", "Dedicated budget or resources for digitalisation"),
]
# Worked example of Section 4.1: C = 7/12, L1 = L2 = L4 = 0.5, L3 = 1/12.
WORKED_EXAMPLE_ANSWERS = [3, 3, 4, 3, 3, 3, 3, 3, 2, 1, 1, 3, 3, 3, 2, 2, 2, 2, 2]


def add_name(workbook, name, reference):
    workbook.defined_names[name] = DefinedName(name, attr_text=reference)


def level_formula(cell):
    """Level 1..5; a value exactly on a bound belongs to the lower level (same rule as the scripts)."""
    return '=1+COUNTIF(bounds,"<"&ROUND(%s,12))' % cell


def set_widths(sheet, widths):
    for column_letter, width in widths.items():
        sheet.column_dimensions[column_letter].width = width


README_TITLE = "ADMA workbook: hand-checkable calculations of the paper"
README_INTRO = [
    "Every number on the calculation sheets is an Excel formula. Yellow cells are inputs you may change; "
    "blue cells are values copied from official sources (each with its link). Changing the yellow cells on "
    "Parameters recalculates every sheet.",
]
README_SECTIONS = [
    ("Sheets and the paper", [
        "Parameters: alpha, delta and level bounds used by all formulas (Section 3.3, Table 2).",
        "Calculator: enter 19 questionnaire answers (1-5) and get layer scores, penalty, ADMI, level, DM_I, DM_S (equations 1-5).",
        "Worked_example: the profile of Section 4.1.",
        "Statistics_mode: Table 7 (equation 6). Uses EU_data and UA_data.",
        "EU_data: Eurostat values for all EU-27 countries; the leader is found with MAX/INDEX/MATCH.",
        "UA_data: Derzhstat values with direct download links.",
        "Diagnostic_situations: Table 6.",
        "Boundary_band: equation (7), the band of base index values in which the penalty changes the level (Section 4.2).",
        "Experiment_sample: the first 1 000 of the 100 000 generated profiles (uniform scenario) with all formulas row by row, "
        "and the corresponding results of the full run for comparison.",
        "Figure_2_band: native Excel chart of the band of equation (7) with the sample profiles whose level the penalty changed.",
        "Figure_3_map: native Excel chart of the diagnostic map (ADMI, DM_I) with the five situations of Table 6.",
    ]),
    ("Full experiment", [
        "The complete experiment (2 x 100 000 profiles, 99 parameter combinations, Tables 4-5, hypotheses H1-H3) is run by scripts/simulation_experiment.py.",
        "The profiles are stored in data/generated/profiles_uniform.csv and data/generated/profiles_low_skewed.csv; "
        "any row can be typed into the Calculator to check it.",
    ]),
    ("Level rule", [
        "Level = 1 + number of bounds strictly below the index value rounded to 12 decimals. A value exactly on a bound "
        "belongs to the lower level: 0.40 is level 2, 0.41 is level 3.",
        "Index values computed from questionnaire answers are multiples of 1/120, so exact ties occur; the rounding removes "
        "floating-point noise so that a tie is never moved to the upper level.",
    ]),
    ("Verification", [
        "scripts/verify_workbook.py evaluates the formulas of this workbook with an independent engine (pycel) and compares "
        "7 159 values with the Python scripts. All values agree.",
        "The workbook is generated by scripts/build_workbook.py from data/raw and data/generated; this README is generated "
        "together with the README sheet and has the same content.",
    ]),
]


def build_readme(sheet):
    sheet["A1"] = README_TITLE
    sheet["A1"].font = TITLE
    row_number = 3
    for paragraph in README_INTRO:
        sheet.cell(row=row_number, column=1, value=paragraph)
        row_number += 1
    for heading, lines in README_SECTIONS:
        row_number += 1
        sheet.cell(row=row_number, column=1, value=heading).font = BOLD
        row_number += 1
        for line in lines:
            sheet.cell(row=row_number, column=1, value=line)
            row_number += 1
    set_widths(sheet, {"A": 160})


def write_readme_markdown(path):
    """Same content as the README sheet, for reading on GitHub without opening Excel."""
    lines = ["# " + README_TITLE, ""]
    lines.extend(README_INTRO)
    for heading, section_lines in README_SECTIONS:
        lines.extend(["", "## " + heading, ""])
        lines.extend("- " + line for line in section_lines)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parameters(workbook):
    sheet = workbook.create_sheet("Parameters")
    sheet["A1"] = "Parameters"
    sheet["A1"].font = TITLE
    rows = [
        ("alpha", CALIBRATED_PARAMETERS["alpha"], "Strength of the weak-link penalty (calibrated value)"),
        ("delta", CALIBRATED_PARAMETERS["delta"], "Threshold of critical layer weakness (calibrated value; 0.375 = mean answer 2.5)"),
    ]
    for row_number, (name, value, description) in enumerate(rows, start=3):
        sheet.cell(row=row_number, column=1, value=name).font = BOLD
        sheet.cell(row=row_number, column=2, value=value).fill = INPUT_FILL
        sheet.cell(row=row_number, column=3, value=description)
    add_name(workbook, "alpha", "Parameters!$B$3")
    add_name(workbook, "delta", "Parameters!$B$4")
    sheet["A6"] = "Level bounds (Table 2)"
    sheet["A6"].font = BOLD
    labels = ["Level 1 | 2", "Level 2 | 3", "Level 3 | 4", "Level 4 | 5"]
    for offset, (label, bound) in enumerate(zip(labels, THEORETICAL_BOUNDS)):
        sheet.cell(row=7 + offset, column=1, value=label)
        sheet.cell(row=7 + offset, column=2, value=bound).fill = INPUT_FILL
    add_name(workbook, "bounds", "Parameters!$B$7:$B$10")
    sheet["A12"] = "Initial values before calibration: alpha = 0.50, delta = 0.25. Model-adjusted bounds used as a robustness check: 0.25, 0.45, 0.60, 0.80."
    set_widths(sheet, {"A": 22, "B": 10, "C": 80})


def build_calculator(workbook, sheet_name, answers, title):
    sheet = workbook.create_sheet(sheet_name)
    sheet["A1"] = title
    sheet["A1"].font = TITLE
    sheet.append([])
    sheet.append(["#", "Block", "Statement", "Answer (1-5)", "Normalised (eq. 1)"])
    for cell in sheet[3]:
        cell.font = BOLD
    validation = DataValidation(type="whole", operator="between", formula1="1", formula2="5", showErrorMessage=True)
    sheet.add_data_validation(validation)
    first_row = 4
    for index, ((block, text), answer) in enumerate(zip(STATEMENTS, answers)):
        row = first_row + index
        sheet.cell(row=row, column=1, value=index + 1)
        sheet.cell(row=row, column=2, value=block)
        sheet.cell(row=row, column=3, value=text)
        answer_cell = sheet.cell(row=row, column=4, value=answer)
        answer_cell.fill = INPUT_FILL
        validation.add(answer_cell)
        sheet.cell(row=row, column=5, value="=(D%d-1)/4" % row)
    last_row = first_row + len(STATEMENTS) - 1
    summary_row = last_row + 2
    sheet.cell(row=summary_row, column=3, value="Result").font = BOLD
    block_rows = {}
    for index, (block, _text) in enumerate(STATEMENTS):
        block_rows.setdefault(block, []).append(first_row + index)
    results = []
    for block in list(ITEMS_PER_LAYER) + ["I", "S"]:
        rows = block_rows[block]
        label = {"I": "DM_I (integration, outside the index)", "S": "DM_S (strategy, outside the index)"}.get(block, "DM_%s (eq. 2)" % block)
        results.append((label, "=AVERAGE(E%d:E%d)" % (rows[0], rows[-1])))
    layer_range = "D%d:D%d" % (summary_row + 1, summary_row + len(ITEMS_PER_LAYER))
    base_row = summary_row + 1 + len(results)
    results.extend([
        ("ADMI_base (eq. 3)", "=AVERAGE(%s)" % layer_range),
        ("DM_min", "=MIN(%s)" % layer_range),
        ("Penalty P (eq. 4)", "=1-alpha*MAX(0,delta-D%d)" % (base_row + 1)),
        ("ADMI (eq. 5)", "=D%d*D%d" % (base_row, base_row + 2)),
        ("Level by ADMI_base", level_formula("D%d" % base_row)),
        ("Level by ADMI", level_formula("D%d" % (base_row + 3))),
        ("Penalty changed the level?", '=IF(D%d<>D%d,"yes","no")' % (base_row + 4, base_row + 5)),
    ])
    for offset, (label, formula) in enumerate(results, start=1):
        sheet.cell(row=summary_row + offset, column=3, value=label)
        sheet.cell(row=summary_row + offset, column=4, value=formula)
    set_widths(sheet, {"A": 4, "B": 7, "C": 78, "D": 14, "E": 18})
    return sheet


def build_data_sheets(workbook):
    """EU_data and UA_data; returns cell references used by Statistics_mode."""
    eu_sheet = workbook.create_sheet("EU_data")
    ua_sheet = workbook.create_sheet("UA_data")
    eu_sheet["A1"] = "Eurostat, ICT usage in enterprises: NACE C10-C12, enterprises with 10+ persons employed, % of enterprises"
    eu_sheet["A1"].font = TITLE
    eu_sheet.cell(row=2, column=1, value="Country").font = BOLD
    eu_sheet.cell(row=3, column=1, value="Source (CSV)").font = BOLD
    countries = list(EU27_COUNTRIES)
    first_country_row = 5
    eu_sheet.cell(row=4, column=1, value="EU27_2020").font = BOLD
    for offset, country in enumerate(countries):
        eu_sheet.cell(row=first_country_row + offset, column=1, value=country)
    last_country_row = first_country_row + len(countries) - 1

    ua_sheet["A1"] = "State Statistics Service of Ukraine, data bank stat.gov.ua (SSSU:DF_INFORM_COMMUN_TECH_ENTRP): KVED 10-12, % of enterprises"
    ua_sheet["A1"].font = TITLE
    ua_sheet.append([])
    ua_sheet.append(["Indicator", "Breakdown", "Year", "Value, %", "Data updated", "Direct download (CSV)"])
    for cell in ua_sheet[3]:
        cell.font = BOLD

    eurostat_cache = {}
    ukrstat_cache = {}
    references = []
    for column_offset, indicator in enumerate(STATISTICS_MODE_INDICATORS):
        column = 2 + column_offset
        eurostat_spec = indicator["eurostat"]
        ukrstat_spec = indicator["ukrstat"]
        if eurostat_spec["dataset"] not in eurostat_cache:
            eurostat_cache[eurostat_spec["dataset"]] = read_csv(RAW_DATA / "eurostat" / ("%s.csv" % eurostat_spec["dataset"]))
        rows = eurostat_cache[eurostat_spec["dataset"]]
        country_values, eu_average, _missing = eurostat_values(rows, eurostat_spec["indicator"], eurostat_spec["year"])
        eu_sheet.cell(row=2, column=column, value="%s %s" % (eurostat_spec["indicator"], eurostat_spec["year"])).font = BOLD
        eu_sheet.cell(row=3, column=column, value=eurostat_url(eurostat_spec["dataset"]))
        eu_sheet.cell(row=4, column=column, value=eu_average).fill = SOURCE_FILL
        for offset, country in enumerate(countries):
            value = country_values.get(country)
            cell = eu_sheet.cell(row=first_country_row + offset, column=column, value=value)
            cell.fill = SOURCE_FILL
        column_letter = eu_sheet.cell(row=1, column=column).column_letter
        country_range = "EU_data!$%s$%d:$%s$%d" % (column_letter, first_country_row, column_letter, last_country_row)

        if ukrstat_spec["file"] not in ukrstat_cache:
            ukrstat_cache[ukrstat_spec["file"]] = read_csv(RAW_DATA / "ukrstat" / "data_bank" / ("%s.csv" % ukrstat_spec["file"]))
        ukraine_value, updated = ukrstat_value(ukrstat_cache[ukrstat_spec["file"]], ukrstat_spec["breakdown_category"], ukrstat_spec["breakdown"], ukrstat_spec["year"])
        ua_row = 4 + column_offset
        ua_sheet.cell(row=ua_row, column=1, value=indicator["name"])
        ua_sheet.cell(row=ua_row, column=2, value="%s / %s" % (ukrstat_spec["breakdown_category"], ukrstat_spec["breakdown"]))
        ua_sheet.cell(row=ua_row, column=3, value=ukrstat_spec["year"])
        ua_sheet.cell(row=ua_row, column=4, value=ukraine_value).fill = SOURCE_FILL
        ua_sheet.cell(row=ua_row, column=5, value=updated)
        ua_sheet.cell(row=ua_row, column=6, value=ukrstat_url(ukrstat_spec["file"]))
        references.append({
            "eu_average": "EU_data!$%s$4" % column_letter,
            "country_range": country_range,
            "country_names": "EU_data!$A$%d:$A$%d" % (first_country_row, last_country_row),
            "ukraine": "UA_data!$D$%d" % ua_row,
        })
    eu_sheet.cell(row=last_country_row + 2, column=1, value="Empty cell = no published value (flag u, low reliability). The CSV links download the full series; filter by indic_is, geo and TIME_PERIOD.")
    ua_sheet.cell(row=4 + len(STATISTICS_MODE_INDICATORS) + 1, column=1,
                  value="Each link downloads a CSV with all years (columns TIME_PERIOD, OBS_VALUE). Interactive table: https://stat.gov.ua/uk/explorer?urn=SSSU%3ADF_INFORM_COMMUN_TECH_ENTRP%28~%29")
    set_widths(eu_sheet, {"A": 14, "B": 14, "C": 14, "D": 14, "E": 14, "F": 14, "G": 14})
    set_widths(ua_sheet, {"A": 32, "B": 42, "C": 8, "D": 10, "E": 14, "F": 120})
    return references


def build_statistics_mode(workbook, references):
    sheet = workbook.create_sheet("Statistics_mode")
    sheet["A1"] = "Table 7. Statistics mode of ADMA for the Ukrainian food-processing industry (equation 6, P_min = 0)"
    sheet["A1"].font = TITLE
    sheet.append([])
    sheet.append(["Layer", "Indicator", "Statement", "Ukraine, %", "Ukraine year", "EU27, %", "EU year", "Leader", "Leader, %", "DM Ukraine", "DM EU27"])
    for cell in sheet[3]:
        cell.font = BOLD
    first_row = 4
    for offset, (indicator, reference) in enumerate(zip(STATISTICS_MODE_INDICATORS, references)):
        row = first_row + offset
        sheet.cell(row=row, column=1, value=indicator["layer"])
        sheet.cell(row=row, column=2, value=indicator["name"])
        sheet.cell(row=row, column=3, value=indicator["statement"])
        sheet.cell(row=row, column=4, value="=%s" % reference["ukraine"])
        sheet.cell(row=row, column=5, value=indicator["ukrstat"]["year"])
        sheet.cell(row=row, column=6, value="=%s" % reference["eu_average"])
        sheet.cell(row=row, column=7, value=indicator["eurostat"]["year"])
        sheet.cell(row=row, column=8, value="=INDEX(%s,MATCH(MAX(%s),%s,0))" % (reference["country_names"], reference["country_range"], reference["country_range"]))
        sheet.cell(row=row, column=9, value="=MAX(%s)" % reference["country_range"])
        sheet.cell(row=row, column=10, value="=D%d/I%d" % (row, row))
        sheet.cell(row=row, column=11, value="=F%d/I%d" % (row, row))
    last_row = first_row + len(STATISTICS_MODE_INDICATORS) - 1
    profile_row = last_row + 2
    sheet.cell(row=profile_row, column=1, value="Layer profile (mean of the layer's indicators)").font = BOLD
    sheet.append(["Layer", "DM Ukraine", "DM EU27", "Ukraine below delta?", "EU27 below delta?"])
    for cell in sheet[profile_row + 1]:
        cell.font = BOLD
    measured_layers = []
    for indicator in STATISTICS_MODE_INDICATORS:
        if indicator["layer"] not in measured_layers:
            measured_layers.append(indicator["layer"])
    for offset, layer in enumerate(measured_layers):
        row = profile_row + 2 + offset
        sheet.cell(row=row, column=1, value=layer)
        sheet.cell(row=row, column=2, value='=AVERAGEIF($A$%d:$A$%d,A%d,$J$%d:$J$%d)' % (first_row, last_row, row, first_row, last_row))
        sheet.cell(row=row, column=3, value='=AVERAGEIF($A$%d:$A$%d,A%d,$K$%d:$K$%d)' % (first_row, last_row, row, first_row, last_row))
        sheet.cell(row=row, column=4, value='=IF(B%d<delta,"yes","no")' % row)
        sheet.cell(row=row, column=5, value='=IF(C%d<delta,"yes","no")' % row)
    note_row = profile_row + 3 + len(measured_layers)
    notes = [
        "L1 (human capital) has no common indicator in the two surveys, so the full ADMI cannot be computed in the statistics mode.",
        "Years differ for three indicators (Section 3.6 of the paper): ICT security documents UA 2023 / EU 2024; IoT UA 2022 / EU 2021.",
        "Leader = EU-27 country with the highest published value; BE, FI and LU publish no values for C10-C12.",
    ]
    for offset, note in enumerate(notes):
        sheet.cell(row=note_row + offset, column=1, value=note)
    set_widths(sheet, {"A": 7, "B": 32, "C": 10, "D": 11, "E": 12, "F": 10, "G": 9, "H": 8, "I": 10, "J": 12, "K": 10})


def build_diagnostic_situations(workbook):
    sheet = workbook.create_sheet("Diagnostic_situations")
    sheet["A1"] = "Table 6. Diagnostic situations of ADMA (illustrative profiles)"
    sheet["A1"].font = TITLE
    sheet.append([])
    sheet.append(["Situation", "DM_C", "DM_L1", "DM_L2", "DM_L3", "DM_L4", "DM_I", "DM_S", "ADMI_base", "DM_min", "Penalty", "ADMI",
                  "Level by ADMI", "Scalar incl. DM_I", "Level by scalar"])
    for cell in sheet[3]:
        cell.font = BOLD
    situations = [
        ("Compliance trap", [0.70, 0.40, 0.45, 0.05, 0.60], 0.30, 0.40),
        ("External EU pressure", [0.35, 0.30, 0.35, 0.30, 0.70], 0.15, 0.30),
        ("Absorptive limiter", [0.55, 0.10, 0.45, 0.45, 0.50], 0.35, 0.40),
        ("Aware mismatch", [0.30, 0.25, 0.25, 0.30, 0.25], 0.20, 0.75),
        ("Illusion of maturity", [0.55, 0.55, 0.55, 0.55, 0.55], 0.15, 0.50),
    ]
    for offset, (name, layers, integration, strategy) in enumerate(situations):
        row = 4 + offset
        sheet.cell(row=row, column=1, value=name)
        for layer_offset, value in enumerate(layers + [integration, strategy]):
            sheet.cell(row=row, column=2 + layer_offset, value=value).fill = INPUT_FILL
        sheet.cell(row=row, column=9, value="=AVERAGE(B%d:F%d)" % (row, row))
        sheet.cell(row=row, column=10, value="=MIN(B%d:F%d)" % (row, row))
        sheet.cell(row=row, column=11, value="=1-alpha*MAX(0,delta-J%d)" % row)
        sheet.cell(row=row, column=12, value="=I%d*K%d" % (row, row))
        sheet.cell(row=row, column=13, value=level_formula("L%d" % row))
        sheet.cell(row=row, column=14, value="=AVERAGE(B%d:G%d)" % (row, row))
        sheet.cell(row=row, column=15, value=level_formula("N%d" % row))
    set_widths(sheet, {"A": 22})


def build_boundary_band(workbook):
    sheet = workbook.create_sheet("Boundary_band")
    sheet["A1"] = "Equation (7): the level drops across bound b if and only if b < ADMI_base <= b / P(DM_min)"
    sheet["A1"].font = TITLE
    sheet["A2"] = "Upper limit is also capped by (4 + DM_min) / 5, the largest base index possible when the weakest layer equals DM_min."
    sheet.append(["Bound b", "DM_min", "Penalty P", "ADMI_base from", "ADMI_base to", "Band width"])
    for cell in sheet[3]:
        cell.font = BOLD
    row = 4
    for bound_offset in range(len(THEORETICAL_BOUNDS)):
        for step in range(16):
            sheet.cell(row=row, column=1, value="=INDEX(bounds,%d)" % (bound_offset + 1))
            sheet.cell(row=row, column=2, value=round(step * 0.025, 3))
            sheet.cell(row=row, column=3, value="=1-alpha*MAX(0,delta-B%d)" % row)
            sheet.cell(row=row, column=4, value="=A%d" % row)
            sheet.cell(row=row, column=5, value="=MIN(A%d/C%d,(4+B%d)/5)" % (row, row, row))
            sheet.cell(row=row, column=6, value="=MAX(0,E%d-A%d)" % (row, row))
            row += 1


def build_experiment_sample(workbook):
    sheet = workbook.create_sheet("Experiment_sample")
    names = column_names()
    path = GENERATED_DATA / "profiles_uniform.csv"
    with io.open(str(path), encoding="utf-8") as handle:
        reader = csv.reader(handle)
        next(reader)
        sample = [next(reader) for _ in range(SAMPLE_SIZE)]
    sheet["A1"] = "First %d of 100 000 generated profiles (uniform scenario, data/generated/profiles_uniform.csv), every column is a formula" % SAMPLE_SIZE
    sheet["A1"].font = TITLE
    headers = ["profile_id"] + names + ["DM_C", "DM_L1", "DM_L2", "DM_L3", "DM_L4", "DM_I", "DM_S", "ADMI_base", "DM_min", "Penalty", "ADMI",
                                        "Level base", "Level ADMI", "Penalised", "Level changed", "Illusion of maturity", "Scalar incl. DM_I", "Scalar level",
                                        "Figure 2: ADMI_base if level changed", "Figure 2: ADMI_base if level kept"]
    header_row = 8
    for column, header in enumerate(headers, start=1):
        sheet.cell(row=header_row, column=column, value=header).font = BOLD
    first_row = header_row + 1
    last_row = first_row + SAMPLE_SIZE - 1
    answer_columns = {name: sheet.cell(row=1, column=2 + index).column_letter for index, name in enumerate(names)}

    def block_range(prefix, item_count, row):
        return "%s%d:%s%d" % (answer_columns["%s_1" % prefix], row, answer_columns["%s_%d" % (prefix, item_count)], row)

    blocks = [(layer, count) for layer, count in ITEMS_PER_LAYER.items()] + [("I", 3), ("S", 2)]
    result_start = 2 + len(names)
    letters = {header: sheet.cell(row=1, column=column).column_letter for column, header in enumerate(headers, start=1)}
    for offset, values in enumerate(sample):
        row = first_row + offset
        for column, value in enumerate(values, start=1):
            sheet.cell(row=row, column=column, value=int(value))
        for block_offset, (prefix, count) in enumerate(blocks):
            sheet.cell(row=row, column=result_start + block_offset, value="=(AVERAGE(%s)-1)/4" % block_range(prefix, count, row))
        layer_range = "%s%d:%s%d" % (letters["DM_C"], row, letters["DM_L4"], row)
        formulas = {
            "ADMI_base": "=AVERAGE(%s)" % layer_range,
            "DM_min": "=MIN(%s)" % layer_range,
            "Penalty": "=1-alpha*MAX(0,delta-%s%d)" % (letters["DM_min"], row),
            "ADMI": "=%s%d*%s%d" % (letters["ADMI_base"], row, letters["Penalty"], row),
            "Level base": level_formula("%s%d" % (letters["ADMI_base"], row)),
            "Level ADMI": level_formula("%s%d" % (letters["ADMI"], row)),
            "Penalised": "=IF(%s%d<1,1,0)" % (letters["Penalty"], row),
            "Level changed": "=IF(%s%d<>%s%d,1,0)" % (letters["Level base"], row, letters["Level ADMI"], row),
            "Illusion of maturity": "=IF(AND(%s%d>=3,%s%d<=0.2),1,0)" % (letters["Level ADMI"], row, letters["DM_I"], row),
            "Scalar incl. DM_I": "=AVERAGE(%s%d:%s%d)" % (letters["DM_C"], row, letters["DM_I"], row),
            "Scalar level": level_formula("%s%d" % (letters["Scalar incl. DM_I"], row)),
            # #N/A leaves a point out of an Excel scatter chart
            "Figure 2: ADMI_base if level changed": "=IF(%s%d=1,%s%d,NA())" % (letters["Level changed"], row, letters["ADMI_base"], row),
            "Figure 2: ADMI_base if level kept": "=IF(%s%d=0,%s%d,NA())" % (letters["Level changed"], row, letters["ADMI_base"], row),
        }
        for header, formula in formulas.items():
            sheet.cell(row=row, column=headers.index(header) + 1, value=formula)

    def column_range(header):
        return "%s%d:%s%d" % (letters[header], first_row, letters[header], last_row)

    full_run = json.loads(SIMULATION_RESULTS.read_text(encoding="utf-8"))["scenarios"]["uniform"]
    summary = [
        ("Share of profiles with a penalty", "=AVERAGE(%s)" % column_range("Penalised"), full_run["H1_calibrated"]["share_penalised"]),
        ("Share of profiles whose level changed (H1)", "=AVERAGE(%s)" % column_range("Level changed"), full_run["H1_calibrated"]["share_level_changed"]),
        ("Mean reduction of the index", "=AVERAGE(%s)-AVERAGE(%s)" % (column_range("ADMI_base"), column_range("ADMI")), full_run["H1_calibrated"]["mean_index_reduction"]),
        ("Share 'illusion of maturity' (H2)", "=AVERAGE(%s)" % column_range("Illusion of maturity"), full_run["H2_integration_masking"]["share_illusion_of_maturity"]),
    ]
    sheet["A2"] = "Summary for this sample"
    sheet["A2"].font = BOLD
    sheet["E2"] = "Full run, 100 000 profiles (scripts/simulation_experiment.py)"
    sheet["E2"].font = BOLD
    for offset, (label, formula, full_value) in enumerate(summary):
        sheet.cell(row=3 + offset, column=1, value=label)
        sheet.cell(row=3 + offset, column=4, value=formula)
        sheet.cell(row=3 + offset, column=5, value=full_value)
    sheet.freeze_panes = sheet.cell(row=first_row, column=2)


def sample_column(workbook, header):
    """Absolute reference to the data rows of one Experiment_sample column, plus its row bounds."""
    sheet = workbook["Experiment_sample"]
    header_row = 8
    for column in range(1, sheet.max_column + 1):
        if sheet.cell(row=header_row, column=column).value == header:
            return column, header_row + 1, header_row + SAMPLE_SIZE
    raise KeyError(header)


def scatter_series(sheet_or_workbook, sheet_name, x_column, y_column, first_row, last_row, title, color, size=3, symbol="circle", line=False, dash=None):
    from openpyxl.chart import Reference, Series
    from openpyxl.chart.marker import Marker
    worksheet = sheet_or_workbook[sheet_name]
    x_values = Reference(worksheet, min_col=x_column, min_row=first_row, max_row=last_row)
    y_values = Reference(worksheet, min_col=y_column, min_row=first_row, max_row=last_row)
    series = Series(y_values, x_values, title=title)
    if line:
        series.marker = Marker(symbol="none")
        series.graphicalProperties.line.solidFill = color
        series.graphicalProperties.line.width = 19050
        if dash:
            series.graphicalProperties.line.dashStyle = dash
    else:
        series.marker = Marker(symbol=symbol, size=size)
        series.marker.graphicalProperties.solidFill = color
        series.marker.graphicalProperties.line.solidFill = color
        series.graphicalProperties.line.noFill = True
    series.smooth = False
    return series


def style_axes(chart, x_title, y_title, x_range, y_range, x_step, y_step):
    chart.x_axis.title = x_title
    chart.y_axis.title = y_title
    chart.x_axis.scaling.min, chart.x_axis.scaling.max = x_range
    chart.y_axis.scaling.min, chart.y_axis.scaling.max = y_range
    chart.x_axis.majorUnit = x_step
    chart.y_axis.majorUnit = y_step
    chart.x_axis.number_format = chart.y_axis.number_format = "0.0"
    chart.x_axis.delete = chart.y_axis.delete = False
    chart.x_axis.majorGridlines = None
    chart.legend.position = "b"


def build_figure_band(workbook):
    """Figure 2: base index versus the weakest layer; the level drops across a bound inside the band of equation (7)."""
    from openpyxl.chart import ScatterChart
    sheet = workbook.create_sheet("Figure_2_band")
    sheet["A1"] = "Figure 2. Where the weak-link penalty changes the maturity level (equation 7; points: first 1 000 profiles of the uniform scenario)"
    sheet["A1"].font = TITLE
    sheet["A2"] = "Between the solid line (bound b) and the dashed line (upper limit of equation 7) the penalty moves the profile one level down. Change alpha or delta on Parameters to see the band move."
    headers = ["DM_min", "Bound 0.40", "Upper limit for 0.40", "Bound 0.60", "Upper limit for 0.60", "Bound 0.20", "Upper limit for 0.20"]
    for column, header in enumerate(headers, start=1):
        sheet.cell(row=4, column=column, value=header).font = BOLD
    first_row = 5
    steps = 16  # DM_min from 0 to 0.375 in steps of 0.025
    for step in range(steps):
        row = first_row + step
        sheet.cell(row=row, column=1, value=round(step * 0.025, 3))
        for column, bound_index in ((2, 2), (4, 3), (6, 1)):
            sheet.cell(row=row, column=column, value="=INDEX(bounds,%d)" % bound_index)
            sheet.cell(row=row, column=column + 1,
                       value="=MIN(%s%d/(1-alpha*MAX(0,delta-A%d)),(4+A%d)/5)" % (sheet.cell(row=row, column=column).column_letter, row, row, row))
    last_row = first_row + steps - 1
    chart = ScatterChart()
    chart.title = "Penalty band and sample profiles"
    chart.style = 13
    chart.height, chart.width = 12, 20
    dm_min_column, sample_first, sample_last = sample_column(workbook, "DM_min")
    kept_column, _, _ = sample_column(workbook, "Figure 2: ADMI_base if level kept")
    changed_column, _, _ = sample_column(workbook, "Figure 2: ADMI_base if level changed")
    chart.series.append(scatter_series(workbook, "Experiment_sample", dm_min_column, kept_column, sample_first, sample_last, "level kept", "BFBFBF", size=3))
    chart.series.append(scatter_series(workbook, "Experiment_sample", dm_min_column, changed_column, sample_first, sample_last, "level changed by the penalty", "C0504D", size=4))
    for column, color, name in ((6, "7F7F7F", "0.20"), (2, "1F4E79", "0.40"), (4, "2E75B6", "0.60")):
        chart.series.append(scatter_series(workbook, "Figure_2_band", 1, column, first_row, last_row, "bound " + name, color, line=True))
        chart.series.append(scatter_series(workbook, "Figure_2_band", 1, column + 1, first_row, last_row, "upper limit " + name, color, line=True, dash="dash"))
    style_axes(chart, "DM_min (weakest layer)", "ADMI_base", (0, 0.6), (0, 0.9), 0.1, 0.1)
    sheet.add_chart(chart, "I4")
    set_widths(sheet, {"A": 9, "B": 11, "C": 19, "D": 11, "E": 19, "F": 11, "G": 19})


def build_figure_map(workbook):
    """Figure 3: diagnostic map in the plane (ADMI, DM_I)."""
    from openpyxl.chart import ScatterChart
    sheet = workbook.create_sheet("Figure_3_map")
    sheet["A1"] = "Figure 3. Diagnostic map (ADMI, DM_I): sample profiles and the five situations of Table 6"
    sheet["A1"].font = TITLE
    sheet["A2"] = "Lower right zone (ADMI above the level-3 bound, DM_I at most 0.20) is the 'illusion of maturity': equipped layers without integration."
    sheet["A4"], sheet["B4"], sheet["C4"] = "Situation", "ADMI", "DM_I"
    for cell in sheet[4]:
        cell.font = BOLD
    situations = ["Compliance trap", "External EU pressure", "Absorptive limiter", "Aware mismatch", "Illusion of maturity"]
    for offset, name in enumerate(situations):
        row = 5 + offset
        sheet.cell(row=row, column=1, value=name)
        sheet.cell(row=row, column=2, value="=Diagnostic_situations!L%d" % (4 + offset))
        sheet.cell(row=row, column=3, value="=Diagnostic_situations!G%d" % (4 + offset))
    sheet["A12"], sheet["B12"], sheet["C12"] = "Guide lines", "x", "y"
    for cell in sheet[12]:
        cell.font = BOLD
    guide_rows = [("level-3 bound", "=INDEX(bounds,2)", 0), ("level-3 bound", "=INDEX(bounds,2)", 1),
                  ("DM_I = 0.20", 0, 0.2), ("DM_I = 0.20", 1, 0.2)]
    for offset, (name, x_value, y_value) in enumerate(guide_rows):
        sheet.cell(row=13 + offset, column=1, value=name)
        sheet.cell(row=13 + offset, column=2, value=x_value)
        sheet.cell(row=13 + offset, column=3, value=y_value)
    chart = ScatterChart()
    chart.title = "Diagnostic map (ADMI, DM_I)"
    chart.style = 13
    chart.height, chart.width = 12, 20
    admi_column, sample_first, sample_last = sample_column(workbook, "ADMI")
    integration_column, _, _ = sample_column(workbook, "DM_I")
    chart.series.append(scatter_series(workbook, "Experiment_sample", admi_column, integration_column, sample_first, sample_last, "sample profiles", "D9D9D9", size=3))
    colors = ["C0504D", "F79646", "9BBB59", "8064A2", "1F4E79"]
    for offset, (name, color) in enumerate(zip(situations, colors)):
        chart.series.append(scatter_series(workbook, "Figure_3_map", 2, 3, 5 + offset, 5 + offset, name, color, size=9, symbol="diamond"))
    chart.series.append(scatter_series(workbook, "Figure_3_map", 2, 3, 13, 14, "level-3 bound", "595959", line=True, dash="dash"))
    chart.series.append(scatter_series(workbook, "Figure_3_map", 2, 3, 15, 16, "DM_I = 0.20", "595959", line=True, dash="dash"))
    style_axes(chart, "ADMI", "DM_I (integration)", (0, 1), (0, 1), 0.2, 0.2)
    sheet.add_chart(chart, "E4")
    set_widths(sheet, {"A": 22, "B": 9, "C": 9})


def main():
    workbook = Workbook()
    build_readme(workbook.active)
    workbook.active.title = "README"
    build_parameters(workbook)
    build_calculator(workbook, "Calculator", WORKED_EXAMPLE_ANSWERS, "ADMI calculator: enter answers 1-5 in the yellow cells")
    build_calculator(workbook, "Worked_example", WORKED_EXAMPLE_ANSWERS, "Section 4.1: worked example (ADMI_base 0.433, level 3 -> ADMI 0.383, level 2)")
    references = build_data_sheets(workbook)
    build_statistics_mode(workbook, references)
    workbook.move_sheet("Statistics_mode", offset=-2)
    build_diagnostic_situations(workbook)
    build_boundary_band(workbook)
    build_experiment_sample(workbook)
    build_figure_band(workbook)
    build_figure_map(workbook)
    for row in workbook["README"].iter_rows():
        for cell in row:
            cell.alignment = WRAP
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(str(OUTPUT_PATH))
    write_readme_markdown(README_PATH)
    print("Saved:", OUTPUT_PATH)
    print("Saved:", README_PATH)


if __name__ == "__main__":
    main()
