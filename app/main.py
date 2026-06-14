"""
FastAPI main — ENSA Kenitra BI API
Entry point for Railway / Replit deployment.
"""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.database import Base, engine, SessionLocal
from app.routers import auth, students, kpi, teachers
from app.security import load_users_from_config, seed_users_from_db, needs_seeding

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s: %(message)s")
logger = logging.getLogger("ensa_bi")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=== ENSA BI API - Demarrage ===")

    # 1. Charger les utilisateurs existants
    load_users_from_config()

    # 2. Tenter la connexion DB et le seeding si necessaire
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("[DB] Tables verifiees / creees.")

        if needs_seeding():
            db = SessionLocal()
            try:
                count_s, count_t = seed_users_from_db(db)
                logger.info(f"[AUTH] Seeding effectue : {count_s} etudiants, {count_t} enseignants")
            finally:
                db.close()
    except Exception as e:
        logger.warning(f"[DB] Non disponible au demarrage : {e}")
        logger.warning("[AUTH] Seeding ignore — DB inaccessible")

    yield
    logger.info("=== ENSA BI API - Arret ===")


app = FastAPI(
    title="ENSA Kenitra — BI API",
    description=(
        "API Business Intelligence securisee pour l'ENSA Kenitra. "
        "Roles : administrateur, direction, enseignant, etudiant. "
        "Authentification JWT."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(students.router)
app.include_router(kpi.router)
app.include_router(teachers.router)


@app.get("/", tags=["Health"])
def root():
    return {
        "service": "ENSA Kenitra BI API",
        "version": "2.0.0",
        "status": "en ligne",
        "docs": "/docs",
        "roles": ["administrateur", "direction", "enseignant", "etudiant"],
    }


@app.get("/healthz", tags=["Health"])
def healthz():
    return {"status": "ok"}
