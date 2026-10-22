"""Indicator configuration, official API addresses and CSV readers.

Two official sources are used:
  * Eurostat, survey "ICT usage in enterprises" (SDMX 2.1 API, SDMX-CSV);
  * State Statistics Service of Ukraine (Derzhstat), data bank stat.gov.ua,
    dataflow SSSU:DF_INFORM_COMMUN_TECH_ENTRP (SDMX 3.0 API, SDMX-CSV).

The same readers parse the raw files stored in data/raw/ and the files freshly
downloaded by statistics_mode_api.py, so both scripts compute identically.
"""

import csv
import io
import ssl
import urllib.request
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA = REPOSITORY_ROOT / "data" / "raw"

EU27_COUNTRIES = "AT BE BG CY CZ DE DK EE EL ES FI FR HR HU IE IT LT LU LV MT NL PL PT RO SE SI SK".split()
FOOD_PROCESSING = "C10-C12"  # NACE Rev. 2 / KVED 10-12

EUROSTAT_API = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/"
EUROSTAT_DATASETS = {
    "isoc_eb_iipn2": "E_ERP1+E_CRM1",
    "isoc_cicce_usen2": "E_CC+E_CC1_S",
    "isoc_eb_iotn2": "E_IOT1+E_IOTDPP",
    "isoc_cisce_ran2": "E_SECMGE1+E_SECPOL2",
}

UKRSTAT_API = "https://stat.gov.ua/sdmx/workspaces/default:integration/registry/sdmx/3.0/data/dataflow/SSSU/DF_INFORM_COMMUN_TECH_ENTRP/~/"
UKRAINE_REGION = "UA00000000000000000"
# Key order: INDICATOR.REGION.BREAKDOWN_CATEGORY.BREAKDOWN.SIZE.NACE.FREQ
UKRSTAT_FILES = {
    "erp": "SH_ENTRP_ERP_SOFTWARE.UA00000000000000000._T._T._T.C10-C12+_T.A",
    "crm": "SH_ENTRP_CRM_SOFTWARE.UA00000000000000000._T._T._T.C10-C12+_T.A",
    "cloud": "SH_ENTRP_CLOUD.UA00000000000000000.CLOUD_COMPUTING_TYPE+_T._T._T.C10-C12+_T.A",
    "ict_security_measures": "SH_ENTRP_ICT_SECURITY.UA00000000000000000.*.*._T.C10-C12+_T.A",
    "ict_security_documents": "SH_ENTRP_HAVE_DOCUMENT.UA00000000000000000._T._T._T.C10-C12+_T.A",
    "iot": "SH_ENTRP_INTERNET_THINGS.UA00000000000000000.*.*._T.C10-C12+_T.A",
}

# Indicators of the statistics mode (Tables 3 and 7 of the paper).
# Each maps one questionnaire statement to a pair of identical survey questions.
STATISTICS_MODE_INDICATORS = [
    {"name": "ERP software", "layer": "C", "statement": 1,
     "eurostat": {"dataset": "isoc_eb_iipn2", "indicator": "E_ERP1", "year": "2025"},
     "ukrstat": {"file": "erp", "breakdown_category": "_T", "breakdown": "_T", "year": "2025"}},
    {"name": "IoT for production processes", "layer": "C", "statement": 2,
     "eurostat": {"dataset": "isoc_eb_iotn2", "indicator": "E_IOTDPP", "year": "2021"},
     "ukrstat": {"file": "iot", "breakdown_category": "PURPOSE_INTERNET_THINGS", "breakdown": "PRODUCTION_PROCESSES", "year": "2022"}},
    {"name": "Document(s) on ICT security", "layer": "C", "statement": 3,
     "eurostat": {"dataset": "isoc_cisce_ran2", "indicator": "E_SECPOL2", "year": "2024"},
     "ukrstat": {"file": "ict_security_documents", "breakdown_category": "_T", "breakdown": "_T", "year": "2023"}},
    {"name": "Internet of Things", "layer": "L2", "statement": 8,
     "eurostat": {"dataset": "isoc_eb_iotn2", "indicator": "E_IOT1", "year": "2021"},
     "ukrstat": {"file": "iot", "breakdown_category": "_T", "breakdown": "_T", "year": "2022"}},
    {"name": "Paid cloud computing services", "layer": "L3", "statement": 10,
     "eurostat": {"dataset": "isoc_cicce_usen2", "indicator": "E_CC", "year": "2025"},
     "ukrstat": {"file": "cloud", "breakdown_category": "CLOUD_COMPUTING_TYPE", "breakdown": "_T", "year": "2025"}},
    {"name": "CRM software", "layer": "L4", "statement": 13,
     "eurostat": {"dataset": "isoc_eb_iipn2", "indicator": "E_CRM1", "year": "2025"},
     "ukrstat": {"file": "crm", "breakdown_category": "_T", "breakdown": "_T", "year": "2025"}},
]


def eurostat_url(dataset):
    return "%s%s/A.GE10.C10-C12+C10-S951_X_K.%s.PC_ENT.?format=SDMX-CSV" % (EUROSTAT_API, dataset, EUROSTAT_DATASETS[dataset])


def ukrstat_url(file_key):
    return UKRSTAT_API + UKRSTAT_FILES[file_key]


def download(url, accept=None):
    """Download a URL and return bytes. Uses certifi if installed (needed on some macOS Python builds)."""
    try:
        import certifi
        context = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        context = ssl.create_default_context()
    headers = {"User-Agent": "adma-reproduction/1.0"}
    if accept:
        headers["Accept"] = accept
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=120, context=context) as response:
        return response.read()


def read_csv(path):
    with io.open(str(path), encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def eurostat_values(rows, indicator, year, nace=FOOD_PROCESSING):
    """Return {country: value} for EU27 countries with a published value, and the EU27 aggregate."""
    countries = {}
    eu_average = None
    missing = []
    for row in rows:
        if row["indic_is"] != indicator or row["TIME_PERIOD"] != year or row["nace_r2"] != nace:
            continue
        value = float(row["OBS_VALUE"]) if row["OBS_VALUE"] else None
        if row["geo"] == "EU27_2020":
            eu_average = value
        elif row["geo"] in EU27_COUNTRIES:
            if value is None:
                missing.append(row["geo"])
            else:
                countries[row["geo"]] = value
    missing.extend(code for code in EU27_COUNTRIES if code not in countries and code not in missing)
    return countries, eu_average, sorted(missing)


def ukrstat_value(rows, breakdown_category, breakdown, year, nace=FOOD_PROCESSING):
    for row in rows:
        if (row["NACE"] == nace and row["TIME_PERIOD"] == year and row["BREAKDOWN_CATEGORY"] == breakdown_category
                and row["BREAKDOWN"] == breakdown and row["SIZE"] == "_T" and row["OBS_VALUE"]):
            return float(row["OBS_VALUE"]), row.get("UPDATED")
    raise KeyError("No Derzhstat value for %s/%s, %s, %s" % (breakdown_category, breakdown, nace, year))
