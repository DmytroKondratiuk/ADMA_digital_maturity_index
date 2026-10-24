"""Ukrainian texts of the package outputs: the Ukrainian workbook (excel/ADMA_workbook_ua.xlsx, excel/README_ua.md)
and the Ukrainian copies of the result files (results/*_ua.json).

Only labels and prose are translated. Identifiers stay the same in both languages: indicator codes, layer codes
(C, L1-L4, I, S), country codes, JSON keys and formula names, so that the two versions can be compared line by line.
"""

import json

COUNTRY_NAMES_UA = {"EU27_2020": "ЄС-27", "DE": "Німеччина", "PL": "Польща", "HU": "Угорщина", "RO": "Румунія",
                    "CZ": "Чехія", "SK": "Словаччина", "LT": "Литва", "LV": "Латвія", "EE": "Естонія",
                    "BG": "Болгарія", "UA": "Україна"}

STRENGTH_UA = {"direct": "пряма", "acceptable": "прийнятна", "proxy": "проксі"}

STATEMENTS_UA = [
    "Програмне забезпечення для планування виробництва та ресурсів (ERP, MES)",
    "Автоматизація виробничих процесів за допомогою цифрового обладнання",
    "Затверджена стратегія або план цифрового розвитку на 2-3 роки",
    "Цифрові інструменти управління персоналом (HRM)",
    "Працівники мають навички роботи з цифровими інструментами",
    "Виробничий персонал вводить первинні дані на мобільних пристроях або терміналах на робочому місці",
    "Цифровий облік запасів (WMS або електронні таблиці)",
    "Збір і аналіз даних про використання ресурсів, відхилення та втрати",
    "Моніторинг умов зберігання за допомогою датчиків або IoT",
    "GPS-моніторинг або телематика на транспорті й техніці",
    "Планування технічного обслуговування на основі даних (CMMS)",
    "Технології точного землеробства або точного тваринництва",
    "Цифрові канали збуту (вебсайт, електронна комерція, EDI)",
    "Систематичний збір і аналіз даних про попит, ціни та відгуки (CRM)",
    "Цифрова простежуваність: перевірена інформація про походження продукції",
    "Автоматична передача виробничих даних між підрозділами",
    "Своєчасне отримання зовнішніх даних (ціни, погода, регулювання)",
    "Інтеграція цифрових систем підприємства між собою",
    "Регулярне відстеження нових цифрових технологій",
    "Окремий бюджет або ресурси на цифровізацію",
    "Оцінювання результатів цифрових проєктів і перегляд планів цифровізації",
]

SHEET_NAMES_UA = {
    "README": "Опис",
    "Parameters": "Параметри",
    "Calculator": "Калькулятор",
    "Worked_example": "Приклад_розрахунку",
    "Statistics_mode": "Статистичний_режим",
    "TOPSIS": "TOPSIS",
    "EU_data": "Дані_ЄС",
    "UA_data": "Дані_України",
    "Diagnostic_situations": "Діагностичні_ситуації",
    "Boundary_band": "Гранична_смуга",
    "Experiment_sample": "Вибірка_експерименту",
    "Figure_2_band": "Рисунок_2_смуга",
    "Figure_3_map": "Рисунок_3_карта",
}

README_TITLE_UA = "Книга ADMA: розрахунки статті, які можна перевірити вручну"
README_INTRO_UA = [
    "Кожне число на розрахункових аркушах є формулою Excel. Жовті клітинки - вхідні дані, які можна змінювати; "
    "блакитні клітинки - значення, перенесені з офіційних джерел (кожне з посиланням). Зміна жовтих клітинок на аркуші "
    "Параметри перераховує всі аркуші.",
    "Це українська версія книги excel/ADMA_workbook.xlsx: формули й числа однакові, перекладено підписи, назви аркушів "
    "і твердження анкети. Коди показників, шарів і країн не перекладаються.",
]
README_SECTIONS_UA = [
    ("Аркуші та стаття", [
        "Параметри: alpha, delta і межі рівнів, які використовують усі формули (розділ 3, таблиця 2).",
        "Калькулятор: введіть 21 відповідь анкети (1-5) і отримайте оцінки шарів, штраф, ADMI, рівень, DM_I, DM_S (рівняння 1-5).",
        "Приклад_розрахунку: профіль з початку розділу 4.",
        "Статистичний_режим: таблиці 5 і 6, харчова промисловість (NACE C10-C12) ЄС-27, Німеччини, дев'яти країн ЦСЄ та України (рівняння 6, P_min = 0). Використовує аркуші Дані_ЄС і Дані_України.",
        "TOPSIS: незалежне ранжування таблиці 6 (ентропійні ваги, близькість до ідеального рішення) і його кореляція Спірмена з ADMI.",
        "Дані_ЄС: значення Євростату для агрегату ЄС-27 і всіх 27 держав-членів; лідера визначають формулами MAX/INDEX/MATCH.",
        "Дані_України: значення Держстату з прямими посиланнями для завантаження.",
        "Діагностичні_ситуації: таблиця 4.",
        "Гранична_смуга: рівняння (7), смуга значень базового індексу, у якій штраф змінює рівень (P1).",
        "Вибірка_експерименту: перші 1 000 із 100 000 згенерованих профілів (рівномірний сценарій) з усіма формулами по рядках "
        "і відповідні результати повного прогону для порівняння.",
        "Рисунок_2_смуга: вбудована діаграма Excel зі смугою рівняння (7) і профілями вибірки, рівень яких змінив штраф.",
        "Рисунок_3_карта: вбудована діаграма Excel з діагностичною картою (ADMI, DM_I) і ситуаціями таблиці 4.",
    ]),
    ("Повний експеримент і статистичний режим", [
        "Повний експеримент (2 x 100 000 профілів, 99 комбінацій параметрів, таблиця 3, додаткова таблиця S2, положення P1-P3) виконує scripts/simulation_experiment.py.",
        "Статистичний режим із перевіркою стійкості до проксі-показників (таблиці 5 і 6, додаткова таблиця S3, положення P4) виконує scripts/statistics_mode_local.py.",
        "Профілі збережено у data/generated/profiles_uniform.csv і data/generated/profiles_low_skewed.csv; "
        "будь-який рядок можна ввести в Калькулятор для перевірки.",
    ]),
    ("Правило визначення рівня", [
        "Рівень = 1 + кількість меж, строго менших за значення індексу, округлене до 12 знаків. Значення, що точно дорівнює "
        "межі, належить до нижчого рівня: 0,40 - рівень 2, 0,41 - рівень 3.",
        "Значення індексу, обчислені з відповідей анкети, кратні 1/60, тому точні збіги з межами трапляються; округлення "
        "усуває похибку обчислень з плаваючою комою, щоб такий збіг ніколи не переносився на вищий рівень.",
    ]),
    ("Перевірка", [
        "scripts/verify_workbook.py обчислює формули цієї книги незалежним рушієм (pycel) і порівнює "
        "7 533 значення з результатами Python-скриптів. Усі значення збігаються.",
        "Книгу генерує scripts/build_workbook.py з data/raw, data/matrix.csv і data/generated; цей README генерується "
        "разом з аркушем Опис і має той самий зміст.",
    ]),
]

# Labels and prose of the workbook, keyed by the English text in build_workbook.py.
WORKBOOK_TEXT_UA = {
    # Parameters
    "Parameters": "Параметри",
    "Strength of the weak-link penalty (calibrated value)": "Сила штрафу за слабку ланку (каліброване значення)",
    "Threshold of critical layer weakness (calibrated value; 0.375 = mean answer 2.5)":
        "Поріг критичної слабкості шару (каліброване значення; 0,375 = середня відповідь 2,5)",
    "Level bounds (Table 2)": "Межі рівнів (таблиця 2)",
    "Level 1 | 2": "Рівень 1 | 2", "Level 2 | 3": "Рівень 2 | 3", "Level 3 | 4": "Рівень 3 | 4", "Level 4 | 5": "Рівень 4 | 5",
    "Initial values before calibration: alpha = 0.50, delta = 0.25. Model-adjusted bounds used as a robustness check: 0.25, 0.45, 0.60, 0.80.":
        "Початкові значення до калібрування: alpha = 0,50, delta = 0,25. Межі, скориговані за моделлю, для перевірки стійкості: 0,25, 0,45, 0,60, 0,80.",
    # Calculator
    "ADMI calculator: enter answers 1-5 in the yellow cells": "Калькулятор ADMI: введіть відповіді 1-5 у жовті клітинки",
    "Worked example of Section 4 (ADMI_base 0.433, level 3 -> ADMI 0.383, level 2)":
        "Приклад розрахунку з розділу 4 (ADMI_base 0,433, рівень 3 -> ADMI 0,383, рівень 2)",
    "Block": "Блок", "Statement": "Твердження", "Answer (1-5)": "Відповідь (1-5)", "Normalised (eq. 1)": "Нормоване (рівн. 1)",
    "Result": "Результат",
    "DM_I (integration, outside the index)": "DM_I (інтеграція, поза індексом)",
    "DM_S (strategy, outside the index)": "DM_S (стратегія, поза індексом)",
    "DM_%s (eq. 2)": "DM_%s (рівн. 2)",
    "ADMI_base (eq. 3)": "ADMI_base (рівн. 3)",
    "Penalty P (eq. 4)": "Штраф P (рівн. 4)",
    "ADMI (eq. 5)": "ADMI (рівн. 5)",
    "Level by ADMI_base": "Рівень за ADMI_base",
    "Level by ADMI": "Рівень за ADMI",
    "Penalty changed the level?": "Штраф змінив рівень?",
    "yes": "так", "no": "ні",
    # EU_data and UA_data
    "Eurostat, ICT usage in enterprises: NACE C10-C12, enterprises with 10+ persons employed, % of enterprises":
        "Євростат, використання ІКТ на підприємствах: NACE C10-C12, підприємства з 10+ зайнятими, % підприємств",
    "Indicator": "Показник", "Year": "Рік", "Source (CSV)": "Джерело (CSV)", "Leader value": "Значення лідера", "Leader": "Лідер",
    "Empty cell = no published value (for example flag u, low reliability). "
    "Leader = member state with the highest published value. The CSV links download the full series; filter by geo and TIME_PERIOD.":
        "Порожня клітинка = значення не опубліковано (наприклад, позначка u, низька надійність). "
        "Лідер = держава-член з найвищим опублікованим значенням. Посилання CSV завантажують повний ряд; фільтруйте за geo і TIME_PERIOD.",
    "State Statistics Service of Ukraine, data bank stat.gov.ua (SSSU:DF_INFORM_COMMUN_TECH_ENTRP): KVED 10-12, enterprises 10+, % of enterprises":
        "Державна служба статистики України, банк даних stat.gov.ua (SSSU:DF_INFORM_COMMUN_TECH_ENTRP): КВЕД 10-12, підприємства 10+, % підприємств",
    "Derzhstat series": "Ряд Держстату", "Value, %": "Значення, %", "Note": "Примітка", "Direct download (CSV)": "Пряме завантаження (CSV)",
    "Each link downloads a CSV with all years and breakdowns (columns BREAKDOWN_CATEGORY, BREAKDOWN, TIME_PERIOD, OBS_VALUE). "
    "Interactive table: https://stat.gov.ua/uk/explorer?urn=SSSU%3ADF_INFORM_COMMUN_TECH_ENTRP%28~%29":
        "Кожне посилання завантажує CSV з усіма роками й розрізами (стовпці BREAKDOWN_CATEGORY, BREAKDOWN, TIME_PERIOD, OBS_VALUE). "
        "Інтерактивна таблиця: https://stat.gov.ua/uk/explorer?urn=SSSU%3ADF_INFORM_COMMUN_TECH_ENTRP%28~%29",
    # Statistics_mode
    "Tables 5 and 6. Statistics mode of ADMA for food processing (NACE C10-C12): layer scores, index and ranking (equation 6, P_min = 0)":
        "Таблиці 5 і 6. Статистичний режим ADMA для харчової промисловості (NACE C10-C12): оцінки шарів, індекс і ранжування (рівняння 6, P_min = 0)",
    "Upper part: every indicator divided by the value of the EU leader. Lower part: layers, ADMI and ranks. EU-27 and Germany are reference rows outside the ranking.":
        "Верхня частина: кожен показник, поділений на значення лідера ЄС. Нижня частина: шари, ADMI і ранги. ЄС-27 і Німеччина - рядки для порівняння поза ранжуванням.",
    "Layer": "Шар", "Strength": "Відповідність", "EU year": "Рік ЄС", "UA year": "Рік UA", "Leader, %": "Лідер, %",
    "Object": "Об'єкт", "Penalty": "Штраф", "Level": "Рівень", "Rank ADMI": "Ранг ADMI", "Rank TOPSIS": "Ранг TOPSIS",
    "Strength of correspondence to the questionnaire statement: direct, acceptable or proxy (Supplementary Table S1).":
        "Відповідність твердженню анкети: пряма, прийнятна або проксі (додаткова таблиця S1).",
    "Years differ for some pairs (Supplementary Table S1). EU-27 and Germany do not enter the ranking.":
        "Для деяких пар роки відрізняються (додаткова таблиця S1). ЄС-27 і Німеччина не входять до ранжування.",
    "The strict set without weak proxies and the leave-one-out check (Supplementary Table S3) are computed by scripts/statistics_mode_local.py.":
        "Строгий набір без слабких проксі та перевірку з вилученням по одному (додаткова таблиця S3) обчислює scripts/statistics_mode_local.py.",
    # TOPSIS
    "TOPSIS ranking of the ten ranked objects of Table 6 on the same five layers, entropy weights":
        "Ранжування TOPSIS десяти об'єктів таблиці 6 за тими самими п'ятьма шарами, ентропійні ваги",
    "Layer score": "Оцінка шару", "Share p = x / column sum": "Частка p = x / сума стовпця", "p * ln p": "p * ln p",
    "Weighted normalised v = w * x / sqrt(sum x^2)": "Зважене нормоване v = w * x / sqrt(sum x^2)",
    "S+ (to ideal)": "S+ (до ідеалу)", "S- (to anti-ideal)": "S- (до антиідеалу)", "Closeness": "Близькість",
    "(rank difference)^2": "(різниця рангів)^2",
    "Entropy e": "Ентропія e", "Divergence 1 - e": "Розбіжність 1 - e", "Entropy weight w": "Ентропійна вага w",
    "Ideal (max v)": "Ідеал (max v)", "Anti-ideal (min v)": "Антиідеал (min v)",
    "Spearman rank correlation ADMI - TOPSIS": "Рангова кореляція Спірмена ADMI - TOPSIS",
    # Diagnostic_situations and Figure_3_map
    "Table 4. Diagnostic situations of ADMA (illustrative profiles)": "Таблиця 4. Діагностичні ситуації ADMA (ілюстративні профілі)",
    "Situation": "Ситуація", "Scalar incl. DM_I": "Скаляр з DM_I", "Level by scalar": "Рівень за скаляром",
    "Compliance trap": "Пастка відповідності",
    "External EU pressure": "Зовнішній тиск ЄС",
    "Absorptive limiter": "Обмежувач абсорбційної здатності",
    "Aware mismatch": "Усвідомлена невідповідність",
    "Illusion of maturity": "Ілюзія зрілості",
    # Boundary_band
    "Equation (7): the level drops across bound b if and only if b < ADMI_base <= b / P(DM_min)":
        "Рівняння (7): рівень знижується через межу b тоді й лише тоді, коли b < ADMI_base <= b / P(DM_min)",
    "Upper limit is also capped by (4 + DM_min) / 5, the largest base index possible when the weakest layer equals DM_min.":
        "Верхню межу також обмежує (4 + DM_min) / 5 - найбільший можливий базовий індекс, коли найслабший шар дорівнює DM_min.",
    "Bound b": "Межа b", "Penalty P": "Штраф P", "ADMI_base from": "ADMI_base від", "ADMI_base to": "ADMI_base до", "Band width": "Ширина смуги",
    # Experiment_sample
    "First %d of 100 000 generated profiles (uniform scenario, data/generated/profiles_uniform.csv), every column is a formula":
        "Перші %d із 100 000 згенерованих профілів (рівномірний сценарій, data/generated/profiles_uniform.csv), кожен стовпець - формула",
    "Level base": "Рівень базовий", "Level ADMI": "Рівень ADMI", "Penalised": "Оштрафовано", "Level changed": "Рівень змінено",
    "Scalar level": "Рівень скаляра",
    "Figure 2: ADMI_base if level changed": "Рисунок 2: ADMI_base, якщо рівень змінено",
    "Figure 2: ADMI_base if level kept": "Рисунок 2: ADMI_base, якщо рівень збережено",
    "Share of profiles with a penalty": "Частка профілів зі штрафом",
    "Share of profiles whose level changed (P1)": "Частка профілів, рівень яких змінився (P1)",
    "Mean reduction of the index": "Середнє зниження індексу",
    "Share 'illusion of maturity' (P2)": "Частка «ілюзії зрілості» (P2)",
    "Summary for this sample": "Підсумок для цієї вибірки",
    "Full run, 100 000 profiles (scripts/simulation_experiment.py)": "Повний прогін, 100 000 профілів (scripts/simulation_experiment.py)",
    # Figure_2_band
    "Figure 2. Where the weak-link penalty changes the maturity level (equation 7; points: first 1 000 profiles of the uniform scenario)":
        "Рисунок 2. Де штраф за слабку ланку змінює рівень зрілості (рівняння 7; точки: перші 1 000 профілів рівномірного сценарію)",
    "Between the solid line (bound b) and the dashed line (upper limit of equation 7) the penalty moves the profile one level down. Change alpha or delta on Parameters to see the band move.":
        "Між суцільною лінією (межа b) і пунктирною лінією (верхня межа рівняння 7) штраф переводить профіль на рівень нижче. Змініть alpha або delta на аркуші Параметри, щоб побачити зсув смуги.",
    "Bound %s": "Межа %s", "Upper limit for %s": "Верхня межа для %s",
    "Penalty band and sample profiles": "Смуга штрафу та профілі вибірки",
    "level kept": "рівень збережено", "level changed by the penalty": "рівень змінено штрафом",
    "bound %s": "межа %s", "upper limit %s": "верхня межа %s",
    "DM_min (weakest layer)": "DM_min (найслабший шар)",
    # Figure_3_map
    "Figure 3. Diagnostic map (ADMI, DM_I): sample profiles and the situations of Table 4":
        "Рисунок 3. Діагностична карта (ADMI, DM_I): профілі вибірки та ситуації таблиці 4",
    "Lower right zone (ADMI above the level-3 bound, DM_I at most 0.20) is the 'illusion of maturity': equipped layers without integration.":
        "Нижня права зона (ADMI вище межі рівня 3, DM_I не більше 0,20) - «ілюзія зрілості»: оснащені шари без інтеграції.",
    "Guide lines": "Допоміжні лінії", "level-3 bound": "межа рівня 3",
    "Diagnostic map (ADMI, DM_I)": "Діагностична карта (ADMI, DM_I)",
    "sample profiles": "профілі вибірки", "DM_I (integration)": "DM_I (інтеграція)",
}

# Derzhstat observation notes (column UA_flag_or_note of data/matrix.csv: "flag ...", the API note, "source ...", joined by "; ").
NOTES_UA = {
    "The information has been compiled on the basis of reports actually submitted by enterprises and additional estimates of indicators.":
        "Інформацію сформовано на основі фактично поданих підприємствами звітів і додаткових оцінок показників.",
}
NOTE_PREFIXES_UA = {"flag ": "позначка ", "source ": "джерело "}


def translate_note(note):
    parts = []
    for part in note.split("; ") if note else []:
        for prefix, prefix_ua in NOTE_PREFIXES_UA.items():
            if part.startswith(prefix):
                part = prefix_ua + part[len(prefix):]
        parts.append(NOTES_UA.get(part, part))
    return "; ".join(parts)


# Text values of the result files; keys and codes are not translated.
RESULTS_TEXT_UA = dict(STRENGTH_UA, **{
    "data/generated/profiles_<scenario>.csv, generated with seed 2026": "data/generated/profiles_<scenario>.csv, згенеровано з seed 2026",
    "P / value of the EU-27 member state with the highest published value (P_min = 0)":
        "P / значення держави-члена ЄС-27 з найвищим опублікованим значенням (P_min = 0)",
})


def translate_values(item):
    """Copy of a result object with its text values in Ukrainian; keys stay unchanged."""
    if isinstance(item, dict):
        return {key: translate_values(value) for key, value in item.items()}
    if isinstance(item, list):
        return [translate_values(value) for value in item]
    if isinstance(item, str):
        return RESULTS_TEXT_UA.get(item, item)
    return item


def ukrainian_path(path):
    return path.with_name(path.stem + "_ua" + path.suffix)


def write_ukrainian_results(path, report):
    """Write <name>_ua.json next to the English result file."""
    output = ukrainian_path(path)
    output.write_text(json.dumps(translate_values(report), ensure_ascii=False, indent=1), encoding="utf-8")
    return output
