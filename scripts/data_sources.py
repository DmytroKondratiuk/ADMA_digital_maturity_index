"""Indicator pairs, official API addresses and the comparison matrix of the statistics mode.

Two official sources are used, both for food processing (NACE Rev. 2 C10-C12, enterprises with 10+ persons
employed, % of enterprises):
  * Eurostat, survey "ICT usage in enterprises" (SDMX 2.1 API, SDMX-CSV; JSON-stat for labels and dates);
  * State Statistics Service of Ukraine (Derzhstat), data bank stat.gov.ua,
    dataflow SSSU:DF_INFORM_COMMUN_TECH_ENTRP (SDMX 3.0 API, SDMX-CSV).

build_matrix() reads the API responses stored in data/raw/eurostat/ict_c10_c12/ and data/raw/ukrstat/ict_c10_c12/
(or a fresh snapshot with the same layout downloaded by statistics_mode_api.py) and returns the comparison matrix: one row per indicator pair with the year used on each
side, the values for EU-27, Germany, nine CEE countries and Ukraine, and the EU leader. data/matrix.csv is this
matrix for the stored data.
"""

import csv
import io
import json
import ssl
import time
import urllib.request
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
DATA = REPOSITORY_ROOT / "data"
RAW_DATA = DATA / "raw"
STATISTICS_FOLDER = "ict_c10_c12"  # subfolder of raw/eurostat/ and raw/ukrstat/ with the statistics-mode API responses
RAW_EUROSTAT = RAW_DATA / "eurostat" / STATISTICS_FOLDER
RAW_UKRSTAT = RAW_DATA / "ukrstat" / STATISTICS_FOLDER
MATRIX_PATH = DATA / "matrix.csv"

EUROSTAT_SDMX_URL = ("https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/"
                     "{dataset}/A.GE10.C10-C12.{indicator}.PC_ENT.?format=SDMX-CSV")
EUROSTAT_JSONSTAT_URL = ("https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
                         "{dataset}?geo=EU27_2020&size_emp=GE10&nace_r2=C10-C12&unit=PC_ENT&lang=EN")
UKRSTAT_DATA_URL = ("https://stat.gov.ua/sdmx/workspaces/default:integration/registry/sdmx/3.0/data/"
                    "dataflow/SSSU/DF_INFORM_COMMUN_TECH_ENTRP/~/"
                    "{indicator}.UA00000000000000000.*.*._T.C10-C12.A")
UKRSTAT_STRUCTURE_URL = ("https://stat.gov.ua/sdmx/workspaces/default:integration/registry/sdmx/3.0/"
                         "structure/dataflow/SSSU/DF_INFORM_COMMUN_TECH_ENTRP/latest?references=all&detail=full")
UKRSTAT_CSV_ACCEPT = "application/vnd.sdmx.data+csv;version=2.0.0"
UKRSTAT_STRUCTURE_ACCEPT = "application/vnd.sdmx.structure+json;version=2.0.0"

EU_AGGREGATE = "EU27_2020"
REFERENCE_COUNTRY = "DE"
CEE_COUNTRIES = ["PL", "HU", "RO", "CZ", "SK", "LT", "LV", "EE", "BG"]
EU_MEMBER_STATES = ["AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "EL", "ES", "FI", "FR", "HR", "HU",
                    "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK"]
MATRIX_COUNTRIES = [EU_AGGREGATE, REFERENCE_COUNTRY] + CEE_COUNTRIES
PREFERRED_YEAR = "2025"

# Each pair: Eurostat dataset + indicator code <-> Derzhstat indicator + breakdown.
# The comparability note was written after reading the labels and definitions on both sides.
INDICATOR_PAIRS = [
    {"pair_id": "ERP", "eurostat_dataset": "isoc_eb_iipn2", "eurostat_indicator": "E_ERP1",
     "ukrstat_indicator": "SH_ENTRP_ERP_SOFTWARE", "ukrstat_breakdown_category": "_T", "ukrstat_breakdown": "_T",
     "comparability_note": "Match: ERP software package to share information between functional areas."},
    {"pair_id": "CRM", "eurostat_dataset": "isoc_eb_iipn2", "eurostat_indicator": "E_CRM1",
     "ukrstat_indicator": "SH_ENTRP_CRM_SOFTWARE", "ukrstat_breakdown_category": "_T", "ukrstat_breakdown": "_T",
     "comparability_note": "Match for 2023+ (E_CRM1 \"as of 2023\"); UA 2022 value corresponds to the older "
                           "Eurostat E_CRM concept (break in series)."},
    {"pair_id": "BI", "eurostat_dataset": "isoc_eb_iipn2", "eurostat_indicator": "E_ITBI",
     "ukrstat_indicator": "SH_ENTRP_BI", "ukrstat_breakdown_category": "_T", "ukrstat_breakdown": "_T",
     "comparability_note": "Match: Business Intelligence software."},
    {"pair_id": "IOT_ANY", "eurostat_dataset": "isoc_eb_iotn2", "eurostat_indicator": "E_IOT1",
     "ukrstat_indicator": "SH_ENTRP_INTERNET_THINGS", "ukrstat_breakdown_category": "_T", "ukrstat_breakdown": "_T",
     "comparability_note": "Match on concept (use of IoT). Eurostat module only in 2021 (E_IOT1), UA only 2022."},
    {"pair_id": "IOT_PRODUCTION", "eurostat_dataset": "isoc_eb_iotn2", "eurostat_indicator": "E_IOTDPP",
     "ukrstat_indicator": "SH_ENTRP_INTERNET_THINGS", "ukrstat_breakdown_category": "PURPOSE_INTERNET_THINGS",
     "ukrstat_breakdown": "PRODUCTION_PROCESSES",
     "comparability_note": "Match: IoT for production processes. Eurostat 2021 only, UA 2022 only."},
    {"pair_id": "ICT_SECURITY_DOCUMENT", "eurostat_dataset": "isoc_cisce_ran2", "eurostat_indicator": "E_SECPOL2",
     "ukrstat_indicator": "SH_ENTRP_HAVE_DOCUMENT", "ukrstat_breakdown_category": "_T", "ukrstat_breakdown": "_T",
     "comparability_note": "Match: identical wording (document(s) on measures, practices or procedures on ICT security)."},
    {"pair_id": "ICT_TRAINING_ICT_SPECIALISTS", "eurostat_dataset": "isoc_ske_ittn2", "eurostat_indicator": "E_ITSPT2",
     "ukrstat_indicator": "ISOC_ENT_ICTT2_SH", "ukrstat_breakdown_category": "DIRECTION_STUDY",
     "ukrstat_breakdown": "FOR_ICT",
     "ukrstat_alternative_indicators": ["SH_ENTRP_TRAIN_ICT"],
     "comparability_note": "Match. UA ISOC_ENT_ICTT2_SH/DIRECTION_STUDY/FOR_ICT repeats SH_ENTRP_TRAIN_ICT "
                           "values for 2018-2022 and extends to 2025."},
    {"pair_id": "ICT_TRAINING_OTHER_EMPLOYEES", "eurostat_dataset": "isoc_ske_ittn2", "eurostat_indicator": "E_ITUST2",
     "ukrstat_indicator": "SH_ENTRP_TRAIN_ICT_OTH", "ukrstat_breakdown_category": "DIRECTION_STUDY",
     "ukrstat_breakdown": "FOR_OTHER",
     "ukrstat_supplement": {"indicator": "ISOC_ENT_ICTT2_SH", "breakdown_category": "DIRECTION_STUDY",
                            "breakdown": "FOR_OTHER"},
     "comparability_note": "Match. UA 2018-2022 from SH_ENTRP_TRAIN_ICT_OTH; 2025 only in "
                           "ISOC_ENT_ICTT2_SH/DIRECTION_STUDY/FOR_OTHER (merged, source recorded per year)."},
    {"pair_id": "ICT_TRAINING_ANY", "eurostat_dataset": "isoc_ske_ittn2", "eurostat_indicator": "E_ITT2",
     "ukrstat_indicator": "ISOC_ENT_ICTT2_SH", "ukrstat_breakdown_category": "_T", "ukrstat_breakdown": "_T",
     "comparability_note": "UA publishes ISOC_ENT_ICTT2_SH for C10-C12 only by breakdown (FOR_ICT / FOR_OTHER), "
                           "no total; the shares cannot be summed (overlap). UA side unavailable."},
    {"pair_id": "ICT_SPECIALISTS_EMPLOYED", "eurostat_dataset": "isoc_ske_itspen2", "eurostat_indicator": "E_ITSP2",
     "ukrstat_indicator": "SH_ENTRP_ICT", "ukrstat_breakdown_category": "_T", "ukrstat_breakdown": "_T",
     "comparability_note": "Match: employs ICT specialists (UA wording: hired specialists for whom ICT is the main job)."},
    {"pair_id": "DATA_ANALYTICS", "eurostat_dataset": "isoc_eb_dan2", "eurostat_indicator": "E_DA",
     "ukrstat_indicator": "SH_ENTRP_BIGDATA", "ukrstat_breakdown_category": "_T", "ukrstat_breakdown": "_T",
     "comparability_note": "Match from UA 2024 (data analytics by own employees or external provider). "
                           "UA 2018-2022 values are the older big-data-analysis concept (break; Eurostat isoc_eb_bdn2)."},
    {"pair_id": "SUPPLY_CHAIN_DATA_EXCHANGE", "eurostat_dataset": "isoc_eb_icsn2", "eurostat_indicator": "E_SISC",
     "ukrstat_indicator": "SH_ENTRP_EXCHANG_DATA", "ukrstat_breakdown_category": "_T", "ukrstat_breakdown": "_T",
     "comparability_note": "Close match: Eurostat \"share supply chain management information electronically with "
                           "suppliers or customers\"; UA \"exchange data electronically with suppliers or customers in "
                           "the supply chain\". No common year."},
    {"pair_id": "PAID_CLOUD", "eurostat_dataset": "isoc_cicce_usen2", "eurostat_indicator": "E_CC",
     "ukrstat_indicator": "SH_ENTRP_CLOUD", "ukrstat_breakdown_category": "CLOUD_COMPUTING_TYPE",
     "ukrstat_breakdown": "_T",
     "ukrstat_supplement": {"indicator": "SH_ENTRP_CLOUD", "breakdown_category": "_T", "breakdown": "_T"},
     "comparability_note": "Match: buy (paid) cloud computing services. UA total is coded "
                           "CLOUD_COMPUTING_TYPE/_T for 2018-2025 and _T/_T for 2026 (merged)."},
    {"pair_id": "MOBILE_INTERNET", "eurostat_dataset": "isoc_cimobe_usen2", "eurostat_indicator": "E_EMPMD2_GT0",
     "ukrstat_indicator": "SH_ENTRP_MOBILE_TELEPHONE", "ukrstat_breakdown_category": "_T", "ukrstat_breakdown": "_T",
     "comparability_note": "Partial match: Eurostat measures providing employees with portable devices that connect "
                           "via mobile telephone networks for business purposes; UA label \"use internet access via "
                           "mobile communication\". Same survey question family, wording differs. Eurostat "
                           "E_MOBBB (mobile broadband) ended 2017, so not used."},
    {"pair_id": "ECOMMERCE_SALES", "eurostat_dataset": "isoc_ec_eseln2", "eurostat_indicator": "E_AESELL",
     "ukrstat_indicator": "SH_NMBR_ECOMMERCE", "ukrstat_breakdown_category": "_T", "ukrstat_breakdown": "_T",
     "comparability_note": "Match on concept (any e-commerce sales, web or EDI). Eurostat survey year X refers "
                           "to sales in year X-1; UA time convention not stated in the API (see README)."},
    {"pair_id": "WEBSITE", "eurostat_dataset": "isoc_ciwebn2", "eurostat_indicator": "E_WEB",
     "ukrstat_indicator": "SH_ENTRP_WEBSITE", "ukrstat_breakdown_category": "_T", "ukrstat_breakdown": "_T",
     "comparability_note": "Match: enterprises with a website."},
    {"pair_id": "EINVOICE_AUTOMATED", "eurostat_dataset": "isoc_eb_icsn2", "eurostat_indicator": "E_INV4S_AP",
     "ukrstat_indicator": "SH_ENTRP_INV", "ukrstat_breakdown_category": "TYPES_ACCOUNTS",
     "ukrstat_breakdown": "ELECTRO_STRUCT_AUTO",
     "ukrstat_alternative_indicators": ["SH_ENTRP_INV_ELECT_AUTOM"],
     "comparability_note": "Match: sending e-invoices in a standard structure suitable for automated processing. "
                           "SH_ENTRP_INV_ELECT_AUTOM exists in the codelist but returns no observations; "
                           "the same concept is published as SH_ENTRP_INV/TYPES_ACCOUNTS/ELECTRO_STRUCT_AUTO."},
    {"pair_id": "AI_ANY", "eurostat_dataset": "isoc_eb_ain2", "eurostat_indicator": "E_AI_TANY",
     "ukrstat_indicator": "SH_ENTRP_AI_TECHNOLOGIES", "ukrstat_breakdown_category": "_T", "ukrstat_breakdown": "_T",
     "comparability_note": "Match: at least one AI technology. Eurostat list of technologies extended in 2025 "
                           "(E_AI_TPVSG: pictures/video/audio); UA added the same item "
                           "(AI_TECHNOLOGY_GEN_MEDIA) only in TIME_PERIOD 2026."},
    {"pair_id": "DII_BASIC_V3", "eurostat_dataset": "isoc_e_diin2", "eurostat_indicator": "E_DI3_GELO",
     "ukrstat_indicator": "SH_ENTRP_BASIC_DIGITAL", "ukrstat_breakdown_category": "_T", "ukrstat_breakdown": "_T",
     "comparability_note": "Concept match (at least basic digital intensity). Eurostat DII version 3 (odd years: "
                           "2021/2023/2025) and version 4 (even years: 2022/2024) use different 12-item sets; "
                           "UA does not state the DII version."},
    {"pair_id": "DII_BASIC_V4", "eurostat_dataset": "isoc_e_diin2", "eurostat_indicator": "E_DI4_GELO",
     "ukrstat_indicator": "SH_ENTRP_BASIC_DIGITAL", "ukrstat_breakdown_category": "_T", "ukrstat_breakdown": "_T",
     "comparability_note": "As DII_BASIC_V3, but the even-year Eurostat version (DII v4, 2022/2024)."},
]

# Statistics mode of ADMA (Table 5 and Supplementary Table S1 of the paper).
# Layer composition: each indicator stands for one questionnaire statement (numbering 1-21 of Table 1).
LAYERS = {
    "C": ["ERP", "IOT_PRODUCTION", "ICT_SECURITY_DOCUMENT"],
    "L1": ["ICT_TRAINING_ICT_SPECIALISTS", "ICT_TRAINING_OTHER_EMPLOYEES"],
    "L2": ["SUPPLY_CHAIN_DATA_EXCHANGE", "DATA_ANALYTICS", "IOT_ANY"],
    "L3": ["MOBILE_INTERNET", "PAID_CLOUD"],
    "L4": ["ECOMMERCE_SALES", "WEBSITE", "CRM"],
}
OUTSIDE_INDEX = {
    "I": ["EINVOICE_AUTOMATED", "BI"],
    "S": ["AI_ANY", "DII_BASIC_V3"],
}
STATEMENT = {
    "ERP": 1, "IOT_PRODUCTION": 2, "ICT_SECURITY_DOCUMENT": 3,
    "ICT_TRAINING_ICT_SPECIALISTS": 5, "ICT_TRAINING_OTHER_EMPLOYEES": 5,
    "SUPPLY_CHAIN_DATA_EXCHANGE": 7, "DATA_ANALYTICS": 8, "IOT_ANY": 9,
    "MOBILE_INTERNET": 10, "PAID_CLOUD": 11,
    "ECOMMERCE_SALES": 13, "WEBSITE": 13, "CRM": 14,
    "EINVOICE_AUTOMATED": 16, "BI": 18, "AI_ANY": 19, "DII_BASIC_V3": 20,
}
STATEMENTS_WITHOUT_INDICATOR = [4, 12, 15, 17]  # no counterpart in the ICT survey
STATEMENTS_NOT_IN_SET = [6, 21]  # added to the questionnaire after the indicator set was formed
# Strength of correspondence between indicator and statement (Supplementary Table S1):
#   direct      the wording coincides with the statement;
#   acceptable  the same practice, measured more broadly or narrowly;
#   proxy       an adjacent practice (weak proxy).
STRENGTH = {
    "ERP": "direct", "IOT_PRODUCTION": "acceptable", "ICT_SECURITY_DOCUMENT": "proxy",
    "ICT_TRAINING_ICT_SPECIALISTS": "acceptable", "ICT_TRAINING_OTHER_EMPLOYEES": "acceptable",
    "SUPPLY_CHAIN_DATA_EXCHANGE": "proxy", "DATA_ANALYTICS": "acceptable", "IOT_ANY": "acceptable",
    "MOBILE_INTERNET": "proxy", "PAID_CLOUD": "proxy",
    "ECOMMERCE_SALES": "direct", "WEBSITE": "direct", "CRM": "direct",
    "EINVOICE_AUTOMATED": "proxy", "BI": "proxy", "AI_ANY": "proxy", "DII_BASIC_V3": "proxy",
}

MATRIX_HEADER = (["pair_id", "eurostat_dataset", "eurostat_indicator", "ukrstat_series",
                  "eurostat_years_EU27", "ukrstat_years", "latest_common_year",
                  "eurostat_year_used", "ukrstat_year_used", "year_gap_years", "year_choice_rule"]
                 + [country + "_value" for country in MATRIX_COUNTRIES]
                 + ["UA_value", "UA_flag_or_note", "leader_country", "leader_value",
                    "eu_member_states_missing", "cee_or_de_missing",
                    "EU27_at_latest_common_year", "UA_at_latest_common_year",
                    "UA_latest_year", "UA_latest_value",
                    "module_aligned_eurostat_year", "EU27_at_module_aligned_year",
                    "status", "comparability_note"])


def download(url, accept=None, retries=5):
    """Download a URL and return text. Uses certifi if installed (needed on some macOS Python builds)."""
    try:
        import certifi
        context = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        context = ssl.create_default_context()
    headers = {"User-Agent": "adma-reproduction/2.0"}
    if accept:
        headers["Accept"] = accept
    last_error = None
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=300, context=context) as response:
                return response.read().decode("utf-8")
        except Exception as error:  # also covers HTTP 429 rate limiting on stat.gov.ua
            last_error = error
            time.sleep(10 * (attempt + 1))
    raise RuntimeError("Download failed: %s (%s)" % (url, last_error))


def eurostat_datasets():
    return sorted({pair["eurostat_dataset"] for pair in INDICATOR_PAIRS})


def ukrstat_indicators():
    codes = []
    for pair in INDICATOR_PAIRS:
        codes.append(pair["ukrstat_indicator"])
        codes.extend(pair.get("ukrstat_alternative_indicators", []))
        if pair.get("ukrstat_supplement"):
            codes.append(pair["ukrstat_supplement"]["indicator"])
    return sorted(set(codes))


def read_eurostat(eurostat_directory, dataset):
    """Observations of one stored Eurostat slice: {(indicator, geo, year): {value, flag, confidentiality}}."""
    path = Path(eurostat_directory) / ("eurostat_%s.csv" % dataset)
    observations = {}
    with io.open(str(path), encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            observations[(row["indic_is"], row["geo"], row["TIME_PERIOD"])] = {
                "value": row["OBS_VALUE"], "flag": row.get("OBS_FLAG", ""), "confidentiality": row.get("CONF_STATUS", "")}
    return observations


def read_ukrstat(ukrstat_directory, indicator):
    """Observations of one stored Derzhstat indicator: {(breakdown category, breakdown, year): {...}}."""
    path = Path(ukrstat_directory) / ("ukrstat_%s.csv" % indicator)
    observations = {}
    with io.open(str(path), encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if not row.get("INDICATOR"):
                continue
            observations[(row["BREAKDOWN_CATEGORY"], row["BREAKDOWN"], row["TIME_PERIOD"])] = {
                "value": row["OBS_VALUE"], "flag": row.get("OBS_FLAG", ""), "note": row.get("NOTES_OBS", "")}
    return observations


def has_number(observation):
    return observation is not None and observation["value"] not in ("", None)


def format_observation(observation):
    if observation is None:
        return ""
    text = observation["value"] or ""
    if observation.get("flag"):
        text = (text + " " if text else "") + "[" + observation["flag"] + "]"
    if observation.get("confidentiality") and not observation["value"]:
        text = (text + " " if text else "") + "[conf:" + observation["confidentiality"] + "]"
    return text


def ukrstat_series(pair, ukrstat_data):
    """{year: observation with source} for the UA side of a pair, merging a supplement series if declared."""
    series = {}
    sources = [(pair["ukrstat_indicator"], pair["ukrstat_breakdown_category"], pair["ukrstat_breakdown"])]
    supplement = pair.get("ukrstat_supplement")
    if supplement:
        sources.append((supplement["indicator"], supplement["breakdown_category"], supplement["breakdown"]))
    for indicator, breakdown_category, breakdown in sources:
        for (category, code, year), observation in ukrstat_data[indicator].items():
            if category == breakdown_category and code == breakdown and has_number(observation) and year not in series:
                merged = dict(observation)
                merged["source"] = "%s/%s/%s" % (indicator, breakdown_category, breakdown)
                series[year] = merged
    return series


def matrix_row(pair, eurostat_observations, ua_series):
    """Year choice, country values and EU leader for one indicator pair."""
    def observation(country, year):
        return eurostat_observations.get((pair["eurostat_indicator"], country, year)) if year else None

    eu_years = sorted(year for (code, country, year), item in eurostat_observations.items()
                      if code == pair["eurostat_indicator"] and country == EU_AGGREGATE and has_number(item))
    ua_years = sorted(ua_series)
    common_years = sorted(set(eu_years) & set(ua_years))
    latest_common = common_years[-1] if common_years else ""
    if PREFERRED_YEAR in eu_years and PREFERRED_YEAR in ua_years:
        eu_year, ua_year, rule = PREFERRED_YEAR, PREFERRED_YEAR, "both sides have 2025"
    else:
        eu_year = eu_years[-1] if eu_years else ""
        ua_candidates = [year for year in ua_years if year <= PREFERRED_YEAR] or ua_years
        ua_year = ua_candidates[-1] if ua_candidates else ""
        rule = "latest available on each side (UA capped at 2025)"
    status = "ok"
    if not eu_years:
        status = "FAILED: no Eurostat EU27 data"
    if not ua_years:
        status = "FAILED: no Ukrstat data" if status == "ok" else status + "; no Ukrstat data"

    row = {"pair_id": pair["pair_id"], "eurostat_dataset": pair["eurostat_dataset"],
           "eurostat_indicator": pair["eurostat_indicator"],
           "ukrstat_series": "%s/%s/%s" % (pair["ukrstat_indicator"], pair["ukrstat_breakdown_category"], pair["ukrstat_breakdown"]),
           "eurostat_years_EU27": " ".join(eu_years), "ukrstat_years": " ".join(ua_years),
           "latest_common_year": latest_common, "eurostat_year_used": eu_year, "ukrstat_year_used": ua_year,
           "year_gap_years": (int(ua_year) - int(eu_year)) if eu_year and ua_year else "",
           "year_choice_rule": rule, "status": status, "comparability_note": pair["comparability_note"]}
    row.update({country + "_value": format_observation(observation(country, eu_year)) for country in MATRIX_COUNTRIES})
    row["cee_or_de_missing"] = " ".join(country for country in MATRIX_COUNTRIES if not has_number(observation(country, eu_year)))

    leader_country, leader_value, missing_members = "", None, []
    for country in EU_MEMBER_STATES:
        item = observation(country, eu_year)
        if not has_number(item):
            missing_members.append(country)
            continue
        numeric = float(item["value"])
        if leader_value is None or numeric > leader_value:
            leader_country, leader_value = country, numeric
        elif numeric == leader_value:
            leader_country += "/" + country
    row["leader_country"] = leader_country
    row["leader_value"] = format_observation(observation(leader_country.split("/")[0], eu_year)) if leader_country else ""
    row["eu_member_states_missing"] = " ".join(missing_members)

    ua_observation = ua_series.get(ua_year)
    row["UA_value"] = ua_observation["value"] if ua_observation else ""
    notes = []
    if ua_observation:
        if ua_observation.get("flag"):
            notes.append("flag " + ua_observation["flag"])
        if ua_observation.get("note"):
            notes.append(ua_observation["note"])
        if ua_observation["source"] != row["ukrstat_series"]:
            notes.append("source " + ua_observation["source"])
    row["UA_flag_or_note"] = "; ".join(notes)
    row["EU27_at_latest_common_year"] = format_observation(observation(EU_AGGREGATE, latest_common))
    row["UA_at_latest_common_year"] = ua_series[latest_common]["value"] if latest_common else ""
    row["UA_latest_year"] = ua_years[-1] if ua_years else ""
    row["UA_latest_value"] = ua_series[ua_years[-1]]["value"] if ua_years else ""
    # From 2022 on, Derzhstat modules appear one survey year after the Eurostat module (IoT EU 2021 / UA 2022).
    # This column gives the EU27 value for (UA year used - 1) as a sensitivity check.
    aligned_year = str(int(ua_year) - 1) if ua_year else ""
    aligned = observation(EU_AGGREGATE, aligned_year)
    row["module_aligned_eurostat_year"] = aligned_year if has_number(aligned) else ""
    row["EU27_at_module_aligned_year"] = format_observation(aligned) if has_number(aligned) else ""
    return row


def build_matrix(raw_root=RAW_DATA):
    """Comparison matrix (one row per indicator pair) from API responses stored under raw_root/{eurostat,ukrstat}/ict_c10_c12/."""
    eurostat_directory = Path(raw_root) / "eurostat" / STATISTICS_FOLDER
    ukrstat_directory = Path(raw_root) / "ukrstat" / STATISTICS_FOLDER
    eurostat_data = {dataset: read_eurostat(eurostat_directory, dataset) for dataset in eurostat_datasets()}
    ukrstat_data = {indicator: read_ukrstat(ukrstat_directory, indicator) for indicator in ukrstat_indicators()}
    return [matrix_row(pair, eurostat_data[pair["eurostat_dataset"]], ukrstat_series(pair, ukrstat_data))
            for pair in INDICATOR_PAIRS]


def write_matrix(rows, path):
    with io.open(str(path), "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MATRIX_HEADER)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def read_matrix(path=MATRIX_PATH):
    with io.open(str(path), encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_value(raw):
    """'41.51 [b]' -> 41.51; '[u]' or '' (value not published) -> None."""
    text = (raw or "").split(" ")[0]
    try:
        return float(text)
    except ValueError:
        return None


def eurostat_metadata(eurostat_directory, dataset):
    """Label, last update and indicator labels of a dataset from the stored JSON-stat response."""
    path = Path(eurostat_directory) / ("eurostat_%s_metadata_EU27.json" % dataset)
    jsonstat = json.loads(path.read_text(encoding="utf-8"))
    return {"label": jsonstat.get("label"), "updated": jsonstat.get("updated"), "dimension_order": jsonstat.get("id"),
            "indicator_labels": jsonstat["dimension"]["indic_is"]["category"]["label"]}
