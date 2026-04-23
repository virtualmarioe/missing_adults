"""Preprocess the SIRDEC open data for the interactive explorer.

Applies the same filters as Ruiz-Rizzo et al. (2022):

* Age and date of missingness must be present.
* Excludes cases classified as presumed forced disappearance.
* Keeps only older adults (age >= 60) at the moment of missingness.
* Excludes "Aparecio Muerto" (found dead) cases.
* Keeps only cases reported inside Colombia.

Outputs a compact JSON payload consumed by the project's index.html.

Usage:
    python3 preprocess.py --in desaparecidos_colombia.csv \
                          --out ../data/cohort.json

The script accesses CSV columns by index so the source file stays
pure ASCII regardless of the editor's encoding.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path


# Column indices in the SIRDEC open-data CSV (observed 2022 dump)
COL_ID = 0
COL_STATUS = 1          # Estado de la desaparicion
COL_CLASSIF = 2         # Clasificacion de la desaparicion
COL_DATE = 3            # Fecha de la desaparicion
COL_AGE = 4             # Edad al momento de la desaparicion
COL_SEX = 5             # Sexo del desaparecido
COL_MARITAL = 8         # Estado civil del desaparecido
COL_EDU = 9             # Escolaridad del desaparecido
COL_VULN = 10           # Factor de vulnerabilidad del desaparecido
COL_COUNTRY = 11        # Pais donde ocurre la desaparicion
COL_MUNI = 12           # Municipio donde ocurre la desaparicion DANE


# Raw categorical values, referenced via unicode escapes so the
# Python source stays ASCII-clean.
STATUS_MISSING = "Desaparecido"
STATUS_FOUND_ALIVE = "Aparecio Vivo"
STATUS_FOUND_DEAD = "Aparecio Muerto"
CLASSIF_FORCED = "Desaparici\u00f3n Presuntamente Forzada"
SEX_MALE = "Hombre"
SEX_FEMALE = "Mujer"
COUNTRY_COLOMBIA = "Colombia"
UNKNOWN_MUNI = "Sin informaci\u00f3n"


# Approximate 2018-2021 DANE populations (in thousands) for the
# most frequent municipalities in the cohort. Anything not listed
# falls into the "<200k" bucket, which is a reasonable default for
# Colombia's small municipalities.
MUNI_POP_THOUSANDS: dict[str, int] = {
    "Bogot\u00e1, D.C.": 7900,
    "Medell\u00edn": 2500,
    "Cali": 2200,
    "Barranquilla": 1200,
    "Cartagena": 1000,
    "C\u00facuta": 700,
    "Soledad": 600,
    "Ibagu\u00e9": 530,
    "Bucaramanga": 580,
    "Soacha": 650,
    "Santa Marta": 500,
    "Villavicencio": 550,
    "Valledupar": 500,
    "Bello": 530,
    "Pereira": 470,
    "Pasto": 450,
    "Manizales": 400,
    "Buenaventura": 330,
    "Neiva": 350,
    "Palmira": 350,
    "Armenia": 300,
    "Popay\u00e1n": 320,
    "Sincelejo": 300,
    "Monter\u00eda": 470,
    "Itag\u00fc\u00ed": 280,
    "Floridablanca": 310,
    "Tulu\u00e1": 220,
    "Envigado": 230,
    "Dosquebradas": 210,
    "Riohacha": 280,
    "Tunja": 180,
    "Girardot": 110,
    "Yopal": 140,
    "Jamund\u00ed": 140,
    "Fusagasug\u00e1": 140,
    "Piedecuesta": 160,
    "Facatativ\u00e1": 140,
    "Apartad\u00f3": 190,
    "Rionegro": 140,
    "Quibd\u00f3": 130,
    "Ocan\u0303a": 100,  # Ocana
}


def pop_bucket(muni: str) -> str:
    pop = MUNI_POP_THOUSANDS.get(muni)
    if pop is None:
        return "<200k"
    if pop >= 4000:
        return ">4M"
    if pop >= 1000:
        return "1M-4M"
    if pop >= 500:
        return "500k-1M"
    if pop >= 200:
        return "200k-500k"
    return "<200k"


def vuln_group(v: str) -> str:
    if not v or v == "Sin informaci\u00f3n":
        return "Unknown"
    if v == "Ninguno":
        return "None reported"
    if v == "Otro":
        return "Other (specified)"
    lo = v.lower()
    if "droga" in lo or "prostituc" in lo:
        return "Substance / lifestyle"
    if "habitante de la calle" in lo or "desplaz" in lo or "reciclador" in lo:
        return "Homeless / displaced"
    if "discapacit" in lo or "herido" in lo or "sanitaria" in lo:
        return "Health / disability"
    group_markers = [
        "campesino",
        "\u00e9tnicos",  # etnicos
        "lgbt",
        "religiosos",
        "comunal",
        "l\u00edder",  # lider
        "periodismo",
        "judiciales",
        "pol\u00edtica",  # politica
        "sindicales",
    ]
    if any(m in lo for m in group_markers):
        return "Social / cultural group"
    return "Other (specified)"


MARITAL_MAP = {
    "Soltero (a)": "Single",
    "Casado (a)": "Married",
    "Uni\u00f3n libre": "Domestic partnership",
    "Viudo (a)": "Widowed",
    "Separado (a), Divorciado (a)": "Separated / divorced",
    "Sin informaci\u00f3n": "Unknown",
}


EDUCATION_MAP = {
    "Sin escolaridad": "None",
    "Educaci\u00f3n inicial y educaci\u00f3n preescolar": "Preschool",
    "Educaci\u00f3n b\u00e1sica primaria": "Primary",
    "Educaci\u00f3n b\u00e1sica secundaria o secundaria baja": "Secondary (lower)",
    "Educaci\u00f3n media o secundaria alta": "Secondary (upper)",
    "Educaci\u00f3n t\u00e9cnica profesional y tecnol\u00f3gica": "Technical",
    "Universitario": "University",
    "Especializaci\u00f3n, Maestr\u00eda o equivalente": "Postgraduate",
    "Doctorado o equivalente": "Postgraduate",
    "Sin informaci\u00f3n": "Unknown",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--in", dest="in_path", required=True, type=Path)
    parser.add_argument("--out", dest="out_path", required=True, type=Path)
    args = parser.parse_args()

    with args.in_path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)
    print(f"Header has {len(header)} columns")
    print(f"Total input rows: {len(rows):,}")

    records: list[list] = []
    date_re = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")

    for r in rows:
        if len(r) <= COL_MUNI:
            continue

        # Age
        try:
            age = int(float(r[COL_AGE]))
        except (ValueError, TypeError):
            continue

        # Date
        m = date_re.match(r[COL_DATE] or "")
        if not m:
            continue
        year = int(m.group(1))
        month = int(m.group(2))

        # Paper filters
        if r[COL_CLASSIF] == CLASSIF_FORCED:
            continue
        if age < 60:
            continue
        if r[COL_STATUS] == STATUS_FOUND_DEAD:
            continue
        if r[COL_COUNTRY] != COUNTRY_COLOMBIA:
            continue

        found = 1 if r[COL_STATUS] == STATUS_FOUND_ALIVE else 0
        sex = r[COL_SEX]
        sex_code = "M" if sex == SEX_MALE else "F" if sex == SEX_FEMALE else "U"

        records.append([
            found,
            sex_code,
            age,
            year,
            month,
            pop_bucket(r[COL_MUNI]),
            vuln_group(r[COL_VULN]),
            MARITAL_MAP.get(r[COL_MARITAL], "Unknown"),
            EDUCATION_MAP.get(r[COL_EDU], "Unknown"),
        ])

    total = len(records)
    found_n = sum(1 for r in records if r[0] == 1)
    print(f"After paper filters: {total:,}")
    print(f"  Found: {found_n:,} | Still missing: {total - found_n:,}")

    # Sanity: distributions
    for idx, name in [
        (1, "sex"),
        (5, "muni_pop_bucket"),
        (6, "vulnerability"),
        (7, "marital"),
        (8, "education"),
    ]:
        c = Counter(r[idx] for r in records)
        print(f"\n{name}: {dict(c.most_common())}")

    payload = {
        "paper": {
            "title": "Predicting the probability of finding missing older adults based on machine learning",
            "doi": "10.1007/s42001-022-00171-x",
            "year": 2022,
            "source": "SIRDEC / Datos Abiertos Colombia",
            "filters": "age >= 60, not dead, not forced disappearance, Colombia only",
        },
        "columns": [
            "found",
            "sex",
            "age",
            "year",
            "month",
            "muni_pop_bucket",
            "vulnerability",
            "marital",
            "education",
        ],
        "bucket_orders": {
            "muni_pop_bucket": [">4M", "1M-4M", "500k-1M", "200k-500k", "<200k"],
            "vulnerability": [
                "None reported",
                "Unknown",
                "Other (specified)",
                "Substance / lifestyle",
                "Homeless / displaced",
                "Health / disability",
                "Social / cultural group",
            ],
            "marital": [
                "Married",
                "Single",
                "Domestic partnership",
                "Widowed",
                "Separated / divorced",
                "Unknown",
            ],
            "education": [
                "None",
                "Preschool",
                "Primary",
                "Secondary (lower)",
                "Secondary (upper)",
                "Technical",
                "University",
                "Postgraduate",
                "Unknown",
            ],
        },
        "records": records,
    }

    args.out_path.parent.mkdir(parents=True, exist_ok=True)
    with args.out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=True, separators=(",", ":"))
    size = args.out_path.stat().st_size
    print(f"\nWrote {args.out_path} ({size/1024:.1f} KB)")


if __name__ == "__main__":
    main()
