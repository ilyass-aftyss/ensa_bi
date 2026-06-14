"""
ETL — Étape 3 : Load
Charge les DataFrames nettoyés dans PostgreSQL (Railway).
Gère les insertions upsert-safe via truncate+insert.
"""
import os
import logging
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

LOAD_ORDER = [
    "filieres", "teachers", "students", "courses",
    "rooms", "grades", "teaching", "schedule",
    "finance", "enrollments",
]

TABLE_MAP = {
    "filieres":    "filieres",
    "students":    "students",
    "courses":     "courses",
    "grades":      "grades",
    "teachers":    "teachers",
    "teaching":    "teaching",
    "rooms":       "rooms",
    "schedule":    "schedule",
    "finance":     "finance",
    "enrollments": "enrollments",
}


def get_engine():
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL non défini. Vérifier le fichier .env")
    return create_engine(DATABASE_URL, pool_pre_ping=True)


def ensure_tables(engine):
    """Crée toutes les tables OLTP si elles n'existent pas encore.
    Applique aussi les migrations de colonnes manquantes (idempotent)."""
    from app.database import Base
    import app.models  # noqa: F401 — enregistre tous les modèles dans Base
    Base.metadata.create_all(bind=engine)
    # Migration : ajouter anomalie_budget si la table existait déjà sans elle
    with engine.begin() as conn:
        conn.execute(text(
            "ALTER TABLE finance ADD COLUMN IF NOT EXISTS anomalie_budget VARCHAR(5)"
        ))
    logger.info("[LOAD] Tables OLTP vérifiées / créées.")


def load_table(engine, name: str, df: pd.DataFrame) -> int:
    if df.empty:
        logger.warning(f"[LOAD] {name} — DataFrame vide, saut")
        return 0
    table = TABLE_MAP.get(name, name)
    try:
        with engine.begin() as conn:
            conn.execute(text(f'TRUNCATE TABLE "{table}" RESTART IDENTITY CASCADE'))
        df.to_sql(table, engine, if_exists="append", index=False, chunksize=500)
        logger.info(f"[LOAD] {name} — {len(df)} lignes chargées dans '{table}'")
        return len(df)
    except Exception as e:
        logger.error(f"[LOAD] {name} — Erreur : {e}")
        raise


def load_all(cleaned: dict[str, pd.DataFrame]) -> dict[str, int]:
    engine = get_engine()
    ensure_tables(engine)   # ← crée les tables si elles n'existent pas
    stats = {}
    for name in LOAD_ORDER:
        df = cleaned.get(name, pd.DataFrame())
        stats[name] = load_table(engine, name, df)
    return stats


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from etl.extract import extract_all
    from etl.transform import transform_all
    raw = extract_all()
    cleaned = transform_all(raw)
    stats = load_all(cleaned)
    print("\nRésumé chargement :")
    for name, count in stats.items():
        print(f"  {name}: {count} lignes")
