# Data

All files in `raw/` are stored exactly as delivered by the official sources; nothing was edited. `raw/MANIFEST.json` lists every file with its source URL, download date, size and SHA-256 checksum.

All series are restricted to enterprises with 10 or more persons employed, expressed as a percentage of enterprises, for manufacture of food products, beverages and tobacco products (NACE Rev. 2 C10–C12 / KVED 10–12) and for the total survey aggregate.

## raw/eurostat/ — Eurostat, survey "ICT usage in enterprises"

SDMX-CSV, all countries and all available years. Columns: `DATAFLOW, LAST UPDATE, freq, size_emp, nace_r2, indic_is, unit, geo, TIME_PERIOD, OBS_VALUE, OBS_FLAG, CONF_STATUS`.

| File | Dataset (DOI) | Indicators | Used in the paper |
|---|---|---|---|
| `isoc_eb_iipn2.csv` | Integration of internal processes by NACE Rev. 2 activity ([10.2908/ISOC_EB_IIPN2](https://doi.org/10.2908/ISOC_EB_IIPN2)) | `E_ERP1` ERP, `E_CRM1` CRM | both, 2025 |
| `isoc_cicce_usen2.csv` | Cloud computing services by NACE Rev. 2 activity ([10.2908/ISOC_CICCE_USEN2](https://doi.org/10.2908/ISOC_CICCE_USEN2)) | `E_CC` paid cloud services, `E_CC1_S` sophisticated cloud services | `E_CC`, 2025 |
| `isoc_eb_iotn2.csv` | Internet of Things by NACE Rev. 2 activity ([10.2908/ISOC_EB_IOTN2](https://doi.org/10.2908/ISOC_EB_IOTN2)) | `E_IOT1` IoT, `E_IOTDPP` IoT for production processes | both, 2021 |
| `isoc_cisce_ran2.csv` | Security policy, measures, risks and staff awareness by NACE Rev. 2 activity ([10.2908/ISOC_CISCE_RAN2](https://doi.org/10.2908/ISOC_CISCE_RAN2)) | `E_SECPOL2` document(s) on ICT security, `E_SECMGE1` any ICT security measure | `E_SECPOL2`, 2024 |
| `isoc_e_esms_metadata.htm` | Reference metadata (ESMS) of the survey | sector coverage, legal basis | coverage statement in the introduction |

Flags in `OBS_FLAG`: `b` break in series, `u` low reliability (value suppressed), `e` estimated, `c` confidential.

## raw/ukrstat/ — State Statistics Service of Ukraine (Derzhstat), survey "Use of ICT at enterprises" (form 1-ICT)

### data_bank/ — data bank stat.gov.ua, dataflow `SSSU:DF_INFORM_COMMUN_TECH_ENTRP` (SDMX 3.0, last updated 16 September 2026)

SDMX-CSV. Key dimensions: `INDICATOR, REGION, BREAKDOWN_CATEGORY, BREAKDOWN, SIZE, NACE, FREQ`; `NACE = C10-C12` is food processing, `_T` is the total.

| File | Indicator code | Content | Used in the paper |
|---|---|---|---|
| `erp.csv` | SH_ENTRP_ERP_SOFTWARE | enterprises using ERP software | 2025 |
| `crm.csv` | SH_ENTRP_CRM_SOFTWARE | enterprises using CRM software | 2025 |
| `cloud.csv` | SH_ENTRP_CLOUD | enterprises buying cloud computing services; up to 2025 the total is stored under `BREAKDOWN_CATEGORY = CLOUD_COMPUTING_TYPE, BREAKDOWN = _T`, from 2026 under `_T / _T` | 2025 |
| `ict_security_documents.csv` | SH_ENTRP_HAVE_DOCUMENT | enterprises with document(s) on ICT security measures, practices or procedures | 2023 |
| `iot.csv` | SH_ENTRP_INTERNET_THINGS | IoT, total (`_T / _T`) and by purpose (`PURPOSE_INTERNET_THINGS / …`) | 2022, total and production processes |
| `ict_security_measures.csv` | SH_ENTRP_ICT_SECURITY | ICT security measures, total and by type | not used (break in series, see below) |

Interactive table: <https://stat.gov.ua/uk/explorer?urn=SSSU%3ADF_INFORM_COMMUN_TECH_ENTRP%28~%29>. API documentation: <https://stat.gov.ua/uk/development-api/sdmx-api-v3>.

### xlsx_tables/ — Derzhstat statistical tables

Downloaded on 9 October 2026 from the archive page <https://ukrstat.gov.ua/operativ/operativ2018/zv/ikt/arh_ikt_u.html> (latest server modification: 16 September 2025). These tables end with survey year 2025; year 2026 is published only in the data bank. They are kept for cross-checking: `vikpt_ns.xlsx` tables 9 (ERP, CRM) and 12 (cloud), `vikpt_int.xlsx` tables 13 (IoT) and 19 (ICT security documents), row "10+11+12", give the same values as the data bank. Note: the TLS certificate of ukrstat.gov.ua had expired at download time; integrity is confirmed by the agreement with the data bank.

### archive_2017_2022.zip

Archive attached to the indicator description page on stat.gov.ua (xls/xlsx, 2017–2022). Not used in the calculations.

### methodology/

| File | Document | Relevance |
|---|---|---|
| `zv_vikt_2024_quality_report.pdf` | Standard quality report of the survey (2024) | reference period (S.5); timeliness and finality of data (S.14.1) |
| `zv_vikt_2022_quality_report.pdf` | Standard quality report (2022) | same, previous cycle |
| `415_2022_methodology.pdf` | Methodological provisions, order No. 415 of 28.12.2022 | list of 12 ICT security measures (up to survey year 2023) |
| `139_2025_methodology.pdf` | Methodological provisions, order No. 139 of 21.08.2025 | survey year 2026; 5 ICT security measures following Commission Regulation (EU) 2025/1310 |
| `126_2026_calculation_method.pdf` | Calculation method of the indicators, order No. 126 of 12.05.2026 | indicator formulas |

## Notes for interpretation

- **Year** is the survey year: the situation in the first quarter of that year (e-commerce: the previous year). Derzhstat publishes only final data, around day 170 of the survey year. Eurostat follows the same convention.
- **Break in "ICT security measures"** (76.2 % in 2023 → 57.6 % in 2026 for KVED 10–12): the 2026 questionnaire lists 5 measures instead of 12; the most common one in 2023 (strong password, 71.4 %) was removed. The series are not comparable, which is why the paper uses the documents indicator.
- **Agriculture (NACE section A)** is not covered by the survey in Ukraine or in the EU.
- **Leader** is the EU-27 country with the highest *published* value; Belgium, Finland and Luxembourg publish no values for C10–C12.
