# Data

*Українська версія: [README_ua.md](README_ua.md)*

All files in `raw/` are stored exactly as delivered by the official sources; nothing was edited. `raw/MANIFEST.json` lists every file with its source URL, download date, size and SHA-256 checksum. `matrix.csv` and `indicators_metadata.json` are derived from `raw/eurostat/ict_c10_c12/` and `raw/ukrstat/ict_c10_c12/` by the scripts.

All statistics-mode series are restricted to manufacture of food products, beverages and tobacco products (NACE Rev. 2 C10–C12 / KVED 10–12), enterprises with 10 or more persons employed, expressed as a percentage of enterprises. Countries: EU-27 aggregate, Germany (reference country), nine CEE countries (PL, HU, RO, CZ, SK, LT, LV, EE, BG) and Ukraine. The leader is the EU-27 member state with the highest published value for the year used; the EU-27 aggregate is not part of the leader pool.

## raw/eurostat/ict_c10_c12/ and raw/ukrstat/ict_c10_c12/ — API responses used by the statistics mode (downloaded 9 October 2026)

| Folder | File | Content |
|---|---|---|
| `raw/eurostat/ict_c10_c12/` | `eurostat_{dataset}.csv` | full SDMX-CSV slice `A.GE10.C10-C12.<all indicators>.PC_ENT.<all geo>`, all years, with OBS_FLAG and CONF_STATUS (EU-27 aggregate and all countries) |
| `raw/eurostat/ict_c10_c12/` | `eurostat_{dataset}_metadata_EU27.json` | JSON-stat response: order of dimensions, indicator labels, `updated` date |
| `raw/ukrstat/ict_c10_c12/` | `ukrstat_{INDICATOR}.csv` | Derzhstat SDMX 3.0 CSV `{INDICATOR}.UA00000000000000000.*.*._T.C10-C12.A` (Ukraine, all breakdowns) |
| `raw/ukrstat/ict_c10_c12/` | `ukrstat_dataflow_annotations.json` | annotations of the dataflow (version 10.0.0, lastUpdatedAt 2026-09-23) |

**Eurostat**, survey "ICT usage in enterprises", SDMX 2.1 API. The dimension order, checked through JSON-stat, is the same for all datasets: `freq, size_emp, nace_r2, indic_is, unit, geo, time`.

| Dataset | Title | Updated | DOI |
|---|---|---|---|
| isoc_eb_iipn2 | Integration of internal processes | 2026-02-27 | [10.2908/ISOC_EB_IIPN2](https://doi.org/10.2908/ISOC_EB_IIPN2) |
| isoc_eb_iotn2 | Internet of Things | 2025-12-11 | [10.2908/ISOC_EB_IOTN2](https://doi.org/10.2908/ISOC_EB_IOTN2) |
| isoc_cisce_ran2 | Security policy, measures, risks and staff awareness | 2026-06-15 | [10.2908/ISOC_CISCE_RAN2](https://doi.org/10.2908/ISOC_CISCE_RAN2) |
| isoc_ske_ittn2 | ICT training of personnel | 2026-06-15 | [10.2908/ISOC_SKE_ITTN2](https://doi.org/10.2908/ISOC_SKE_ITTN2) |
| isoc_ske_itspen2 | Enterprises that employ ICT specialists | 2026-06-15 | [10.2908/ISOC_SKE_ITSPEN2](https://doi.org/10.2908/ISOC_SKE_ITSPEN2) |
| isoc_eb_dan2 | Data analytics | 2026-02-27 | [10.2908/ISOC_EB_DAN2](https://doi.org/10.2908/ISOC_EB_DAN2) |
| isoc_eb_icsn2 | Integration with customers/suppliers, supply chain management | 2025-12-11 | [10.2908/ISOC_EB_ICSN2](https://doi.org/10.2908/ISOC_EB_ICSN2) |
| isoc_cicce_usen2 | Cloud computing services | 2026-02-27 | [10.2908/ISOC_CICCE_USEN2](https://doi.org/10.2908/ISOC_CICCE_USEN2) |
| isoc_cimobe_usen2 | Use of mobile connections to the internet | 2025-12-11 | [10.2908/ISOC_CIMOBE_USEN2](https://doi.org/10.2908/ISOC_CIMOBE_USEN2) |
| isoc_ec_eseln2 | E-commerce sales of enterprises | 2026-06-15 | [10.2908/ISOC_EC_ESELN2](https://doi.org/10.2908/ISOC_EC_ESELN2) |
| isoc_ciwebn2 | Websites and functionalities | 2026-02-27 | [10.2908/ISOC_CIWEBN2](https://doi.org/10.2908/ISOC_CIWEBN2) |
| isoc_eb_ain2 | Artificial intelligence | 2026-06-15 | [10.2908/ISOC_EB_AIN2](https://doi.org/10.2908/ISOC_EB_AIN2) |
| isoc_e_diin2 | Digital intensity | 2026-02-27 | [10.2908/ISOC_E_DIIN2](https://doi.org/10.2908/ISOC_E_DIIN2) |

**Derzhstat**, data bank stat.gov.ua, SDMX 3.0, dataflow `SSSU:DF_INFORM_COMMUN_TECH_ENTRP(10.0.0)` "Use of information and communication technologies at enterprises" (code 3.03.00.02), requested with `Accept: application/vnd.sdmx.data+csv;version=2.0.0`. Data updated 16 September 2026. `SIZE=_T` is the whole survey population, i.e. enterprises with 10+ persons employed (1 942 enterprises in KVED 10–12 in 2025). Unit code 1010 is per cent. Interactive table: <https://stat.gov.ua/uk/explorer?urn=SSSU%3ADF_INFORM_COMMUN_TECH_ENTRP%28~%29>. API documentation: <https://stat.gov.ua/uk/development-api/sdmx-api-v3>.

## Indicator pairs and their use in ADMA

Statement numbers follow Table 1 of the paper (21 statements). Strength of correspondence: *direct* (the wording coincides), *acceptable* (the same practice, measured more broadly or narrowly), *proxy* (an adjacent practice).

| Pair | Eurostat (dataset / code) | Derzhstat series | ADMA layer, statement, strength |
|---|---|---|---|
| ERP | iipn2 / E_ERP1 | SH_ENTRP_ERP_SOFTWARE | C, 1, direct |
| IOT_PRODUCTION | iotn2 / E_IOTDPP | SH_ENTRP_INTERNET_THINGS / PURPOSE_INTERNET_THINGS / PRODUCTION_PROCESSES | C, 2, acceptable |
| ICT_SECURITY_DOCUMENT | cisce_ran2 / E_SECPOL2 | SH_ENTRP_HAVE_DOCUMENT | C, 3, proxy of the strategy statement |
| ICT_TRAINING_ICT_SPECIALISTS | ske_ittn2 / E_ITSPT2 | ISOC_ENT_ICTT2_SH / DIRECTION_STUDY / FOR_ICT | L1, 5, acceptable |
| ICT_TRAINING_OTHER_EMPLOYEES | ske_ittn2 / E_ITUST2 | SH_ENTRP_TRAIN_ICT_OTH (2018–2022) and ISOC_ENT_ICTT2_SH / DIRECTION_STUDY / FOR_OTHER (2025) | L1, 5, acceptable |
| SUPPLY_CHAIN_DATA_EXCHANGE | icsn2 / E_SISC | SH_ENTRP_EXCHANG_DATA | L2, 7, proxy of inventory accounting |
| DATA_ANALYTICS | dan2 / E_DA | SH_ENTRP_BIGDATA | L2, 8, acceptable |
| IOT_ANY | iotn2 / E_IOT1 | SH_ENTRP_INTERNET_THINGS | L2, 9, acceptable |
| MOBILE_INTERNET | cimobe_usen2 / E_EMPMD2_GT0 | SH_ENTRP_MOBILE_TELEPHONE | L3, 10, proxy of telematics |
| PAID_CLOUD | cicce_usen2 / E_CC | SH_ENTRP_CLOUD | L3, 11, proxy of data-based maintenance |
| ECOMMERCE_SALES | eseln2 / E_AESELL | SH_NMBR_ECOMMERCE | L4, 13, direct |
| WEBSITE | ciwebn2 / E_WEB | SH_ENTRP_WEBSITE | L4, 13, direct |
| CRM | iipn2 / E_CRM1 | SH_ENTRP_CRM_SOFTWARE | L4, 14, direct |
| EINVOICE_AUTOMATED | icsn2 / E_INV4S_AP | SH_ENTRP_INV / TYPES_ACCOUNTS / ELECTRO_STRUCT_AUTO | I (outside the index), 16, proxy |
| BI | iipn2 / E_ITBI | SH_ENTRP_BI | I (outside the index), 18, proxy |
| AI_ANY | ain2 / E_AI_TANY | SH_ENTRP_AI_TECHNOLOGIES | S (outside the index), 19, proxy |
| DII_BASIC_V3 | e_diin2 / E_DI3_GELO | SH_ENTRP_BASIC_DIGITAL | S (outside the index), 20, proxy |
| ICT_TRAINING_ANY, ICT_SPECIALISTS_EMPLOYED, DII_BASIC_V4 | ske_ittn2 / E_ITT2, ske_itspen2 / E_ITSP2, e_diin2 / E_DI4_GELO | see `matrix.csv` | not used |

Statements 4, 12, 15 and 17 have no counterpart in the ICT survey; statements 6 and 21 were added to the questionnaire after the indicator set was formed. The comparability note of every pair, written after reading the labels and definitions on both sides, is in `matrix.csv` and `scripts/data_sources.py`; labels, definitions and update dates are in `indicators_metadata.json`.

## Year rule

1. If both sides have 2025, 2025 is used.
2. Otherwise the latest available year on each side is used (for Ukraine not later than 2025), and the difference is recorded in `year_gap_years` (UA year minus EU year).

From 2022 on, Derzhstat survey modules appear one survey year later than the corresponding Eurostat modules (IoT: EU 2021, UA 2022; ICT security document: EU 2022, UA 2023; BI and data analytics sources: EU 2023, UA 2024; generative AI for media: EU 2025, UA 2026). Up to 2020 the years coincide. The API does not state the reason. Column `EU27_at_module_aligned_year` gives the EU-27 value for (UA year − 1) as a sensitivity check.

## Flags and gaps

- Eurostat flags: `b` break in series, `u` low reliability (value not published), `d` definition differs, `[conf:C]` confidential.
- Missing values among the countries of Table 5: HU for SUPPLY_CHAIN_DATA_EXCHANGE 2023 (`u`); the layer score of Hungary for L2 is then the mean of its other indicators.
- Member states without a value for the year used are listed in `eu_member_states_missing`; usually BE, FI and LU.
- Derzhstat observation notes (`NOTES_OBS`) are copied to `UA_flag_or_note`. Data from 2022 on exclude the temporarily occupied territories and the territories of active hostilities.
- ICT_TRAINING_ANY could not be paired: for KVED 10–12 Derzhstat publishes ISOC_ENT_ICTT2_SH only by breakdown, and the shares cannot be summed.

## raw/eurostat/isoc_e_esms_metadata.htm

Reference metadata (ESMS) of the survey "ICT usage in enterprises"; it documents the sector coverage cited in the introduction of the paper (the survey does not cover NACE section A).

## raw/ukrstat/ — documentation and cross-check

### xlsx_tables/

Derzhstat statistical tables downloaded on 9 October 2026 from the archive page <https://ukrstat.gov.ua/operativ/operativ2018/zv/ikt/arh_ikt_u.html> (latest server modification: 16 September 2025). They end with survey year 2025 and are kept for cross-checking the data bank. Note: the TLS certificate of ukrstat.gov.ua had expired at download time; integrity is confirmed by the agreement with the data bank.

### archive_2017_2022.zip

Archive attached to the indicator description page on stat.gov.ua (xls/xlsx, 2017–2022). Not used in the calculations.

### methodology/

| File | Document | Relevance |
|---|---|---|
| `zv_vikt_2024_quality_report.pdf` | Standard quality report of the survey (2024) | reference period (S.5); timeliness and finality of data (S.14.1) |
| `zv_vikt_2022_quality_report.pdf` | Standard quality report (2022) | same, previous cycle |
| `415_2022_methodology.pdf` | Methodological provisions, order No. 415 of 28.12.2022 | survey content up to survey year 2025 |
| `139_2025_methodology.pdf` | Methodological provisions, order No. 139 of 21.08.2025 | survey year 2026, following Commission Regulation (EU) 2025/1310 |
| `126_2026_calculation_method.pdf` | Calculation method of the indicators, order No. 126 of 12.05.2026 | indicator formulas |

## Notes for interpretation

- **Year** is the survey year: the situation in the first quarter of that year (e-commerce: the previous year). Derzhstat publishes only final data, around day 170 of the survey year. Eurostat follows the same convention.
- **Agriculture (NACE section A)** is not covered by the ICT survey in Ukraine or in the EU.

## generated/

`profiles_uniform.csv` and `profiles_low_skewed.csv`: 100 000 synthetic questionnaires each (seed 2026), one row per profile with the 21 Likert answers in questionnaire order (`C_1..C_3, L1_1..L1_3, L2_1..L2_3, L3_1..L3_3, L4_1..L4_3, I_1..I_3, S_1..S_3`). Uniform scenario: every answer 1–5 with probability 0.2. Low-skewed scenario: probabilities 0.30, 0.30, 0.20, 0.13, 0.07.
