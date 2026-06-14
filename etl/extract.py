"""
ETL — Étape 1 : Extract
Lit les fichiers CSV depuis data/raw/ et retourne des DataFrames.
"""
import os
import pandas as pd
import logging

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "..", "data", "raw")


def extract_table(table_name: str) -> pd.DataFrame:
    path = os.path.join(RAW_DIR, f"{table_name}.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Fichier introuvable : {path}")
    df = pd.read_csv(path, encoding="utf-8", low_memory=False)
    logger.info(f"[EXTRACT] {table_name}: {len(df)} lignes chargées.")
    return df


def extract_all() -> dict[str, pd.DataFrame]:
    tables = [
        "filieres", "students", "courses", "grades",
        "teachers", "teaching", "rooms", "schedule",
        "finance", "enrollments"
    ]
    data = {}
    for t in tables:
        try:
            data[t] = extract_table(t)
        except FileNotFoundError as e:
            logger.warning(str(e))
            data[t] = pd.DataFrame()
    return data


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    data = extract_all()
    for name, df in data.items():
        print(f"  {name}: {len(df)} lignes, {len(df.columns)} colonnes")
