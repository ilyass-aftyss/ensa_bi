"""
ETL — Étape 2 : Transform
Nettoyage, déduplication, normalisation et validation qualité.
"""
import pandas as pd
import numpy as np
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def _log(df: pd.DataFrame, name: str, action: str):
    logger.info(f"[TRANSFORM] {name} — {action} ({len(df)} lignes restantes)")


def transform_filieres(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset=["id"]).copy()
    df["nom"] = df["nom"].str.strip().str.upper()
    df["description"] = df["description"].fillna("Non renseigné")
    _log(df, "filieres", "nettoyée")
    return df


def transform_students(df: pd.DataFrame) -> pd.DataFrame:
    initial = len(df)
    df = df.drop_duplicates(subset=["id"]).copy()

    # Email manquant → adresse générique
    mask_email = df["email"].isna() | (df["email"] == "")
    df.loc[mask_email, "email"] = (
        df.loc[mask_email, "prenom"].str.lower().str.replace(" ", "")
        + "."
        + df.loc[mask_email, "nom"].str.lower().str.replace(" ", "")
        + ".nc@uit.ac.ma"
    )

    # Normalisation
    for col in ["nom", "prenom"]:
        df[col] = df[col].str.strip().str.title()

    df["sexe"] = df["sexe"].fillna("N")
    df["ville_origine"] = df["ville_origine"].fillna("Non renseigné")

    # Date naissance
    df["date_naissance"] = pd.to_datetime(df["date_naissance"], errors="coerce")
    invalid_dates = df["date_naissance"].isna().sum()
    if invalid_dates:
        logger.warning(f"[TRANSFORM] students — {invalid_dates} dates de naissance invalides")

    # Cohérence annee_cursus
    df["annee_cursus"] = pd.to_numeric(df["annee_cursus"], errors="coerce").fillna(1).astype(int)
    df["annee_cursus"] = df["annee_cursus"].clip(1, 5)

    dropped = initial - len(df)
    if dropped > 0:
        logger.info(f"[TRANSFORM] students — {dropped} doublons supprimés")
    _log(df, "students", "nettoyée")
    return df


def transform_courses(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset=["id"]).copy()
    df["nom"] = df["nom"].str.strip()
    df["semestre"] = df["semestre"].fillna("S1")
    df["credits"] = pd.to_numeric(df["credits"], errors="coerce").fillna(3).astype(int)
    _log(df, "courses", "nettoyée")
    return df


def transform_grades(df: pd.DataFrame) -> pd.DataFrame:
    initial = len(df)
    df = df.drop_duplicates().copy()

    # Conversion notes
    df["note"] = pd.to_numeric(df["note"], errors="coerce")

    # Suppression incohérences : notes hors [0,20]
    invalid_notes = ((df["note"] < 0) | (df["note"] > 20)).sum()
    if invalid_notes:
        logger.warning(f"[TRANSFORM] grades — {invalid_notes} notes hors [0,20] supprimées")
    df = df[df["note"].isna() | ((df["note"] >= 0) & (df["note"] <= 20))]

    df["semestre"] = pd.to_numeric(df["semestre"], errors="coerce").fillna(1).astype(int)
    df["annee_universitaire"] = df["annee_universitaire"].str.strip()

    dropped = initial - len(df)
    logger.info(f"[TRANSFORM] grades — {dropped} lignes incohérentes retirées")
    _log(df, "grades", "nettoyée")
    return df


def transform_teachers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset=["id"]).copy()
    for col in ["nom", "prenom"]:
        df[col] = df[col].str.strip().str.title()
    df["salaire"] = pd.to_numeric(df["salaire"], errors="coerce")
    # Imputation médiane pour salaires manquants
    median_sal = df["salaire"].median()
    missing_sal = df["salaire"].isna().sum()
    df["salaire"] = df["salaire"].fillna(median_sal)
    if missing_sal:
        logger.info(f"[TRANSFORM] teachers — {missing_sal} salaires imputés à la médiane ({median_sal:.0f})")
    df["grade"] = df["grade"].fillna("Enseignant-Chercheur")
    _log(df, "teachers", "nettoyée")
    return df


def transform_finance(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset=["id"]).copy()
    df["budget"] = pd.to_numeric(df["budget"], errors="coerce").fillna(0)
    df["depenses"] = pd.to_numeric(df["depenses"], errors="coerce").fillna(0)

    # Recalcul cohérence taux
    df["taux_execution_pct"] = np.where(
        df["budget"] > 0,
        (df["depenses"] / df["budget"] * 100).round(2),
        0.0
    )

    # Signalement dépenses > budget
    anomalies = (df["depenses"] > df["budget"]).sum()
    if anomalies:
        logger.warning(f"[TRANSFORM] finance — {anomalies} lignes où dépenses > budget (signalées)")
        df["anomalie_budget"] = df["depenses"] > df["budget"]
    else:
        df["anomalie_budget"] = False

    _log(df, "finance", "nettoyée")
    return df


def transform_enrollments(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset=["id"]).copy()
    # Statut manquant → "inscrit" par défaut
    df["statut"] = df["statut"].fillna("inscrit")
    df = df[df["statut"].isin(["inscrit", "abandonné", "diplômé"])]
    _log(df, "enrollments", "nettoyée")
    return df


def transform_all(raw: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    transformers = {
        "filieres":    transform_filieres,
        "students":    transform_students,
        "courses":     transform_courses,
        "grades":      transform_grades,
        "teachers":    transform_teachers,
        "finance":     transform_finance,
        "enrollments": transform_enrollments,
    }
    cleaned = {}
    for name, df in raw.items():
        if df.empty:
            logger.warning(f"[TRANSFORM] {name} vide, ignorée")
            cleaned[name] = df
            continue
        fn = transformers.get(name)
        cleaned[name] = fn(df) if fn else df
    return cleaned


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from etl.extract import extract_all
    raw = extract_all()
    cleaned = transform_all(raw)
    for name, df in cleaned.items():
        print(f"  {name}: {len(df)} lignes après transformation")
