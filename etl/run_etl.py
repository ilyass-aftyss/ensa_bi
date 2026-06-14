"""
ETL Runner — Orchestrateur complet.
Usage : python -m etl.run_etl [--generate]

Flags :
  --generate   Régénère les données brutes avant l'ETL.
  --no-load    Effectue uniquement extract + transform (dry-run).
"""
import sys
import logging
import time
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("etl.runner")


def run(generate: bool = False, dry_run: bool = False):
    start = time.time()
    logger.info("=" * 60)
    logger.info(f"  ETL ENSA KÉNITRA — Démarrage {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    logger.info("=" * 60)

    if generate:
        logger.info("📂 Étape 0 — Génération des données brutes...")
        from etl.generate_data import generate_all
        stats = generate_all()
        logger.info(f"   Généré : {stats}")

    logger.info("📥 Étape 1 — Extraction...")
    from etl.extract import extract_all
    raw = extract_all()
    for name, df in raw.items():
        logger.info(f"   {name}: {len(df)} lignes extraites")

    logger.info("🔧 Étape 2 — Transformation...")
    from etl.transform import transform_all
    cleaned = transform_all(raw)
    for name, df in cleaned.items():
        logger.info(f"   {name}: {len(df)} lignes après nettoyage")

    if not dry_run:
        logger.info("📤 Étape 3 — Chargement PostgreSQL...")
        from etl.load import load_all
        stats = load_all(cleaned)
        total = sum(stats.values())
        logger.info(f"   Total chargé : {total:,} lignes")
    else:
        logger.info("⏭  Étape 3 — SAUTÉE (dry-run)")
        stats = {}

    elapsed = round(time.time() - start, 2)
    logger.info("=" * 60)
    logger.info(f"  ETL terminé en {elapsed}s")
    logger.info("=" * 60)
    return stats


if __name__ == "__main__":
    args = sys.argv[1:]
    generate = "--generate" in args
    dry_run = "--no-load" in args
    run(generate=generate, dry_run=dry_run)
