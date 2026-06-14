"""
Création du Data Warehouse (schéma en étoile) + peuplement des tables de dimensions/faits.
À exécuter après l'ETL (run_etl.py) pour construire le DW analytique.
"""
import os
import logging
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger("warehouse")

DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)


def get_engine():
    return create_engine(DATABASE_URL, pool_pre_ping=True)


def apply_schema(engine):
    schema_path = os.path.join(os.path.dirname(__file__), "star_schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()
    # Split on double newlines to handle multi-statement blocks
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    with engine.begin() as conn:
        for stmt in statements:
            try:
                conn.execute(text(stmt))
            except Exception as e:
                logger.warning(f"SQL warning (ignoré) : {e}")
    logger.info("Schéma en étoile appliqué.")


def populate_dim_time(engine):
    rows = []
    for ay in ["2020-2021","2021-2022","2022-2023","2023-2024","2024-2025"]:
        yr = int(ay[:4])
        for sem in [1, 2]:
            rows.append({
                "annee_universitaire": ay,
                "annee": yr,
                "semestre": sem,
                "periode": f"S{sem+4} {ay}",
            })
    df = pd.DataFrame(rows)
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE dim_time RESTART IDENTITY CASCADE"))
    df.to_sql("dim_time", engine, if_exists="append", index=False)
    logger.info(f"dim_time: {len(df)} périodes insérées.")


def populate_dimensions(engine):
    # dim_filiere
    filieres = pd.read_sql("SELECT id as filiere_id, nom, description FROM filieres", engine)
    filieres["departement"] = filieres["nom"].map({
        "GI-BD": "Informatique et Mathématiques",
        "GI-GL": "Informatique et Mathématiques",
        "GSTR":  "Génie Électrique et Réseaux",
        "GINDUS":"Génie Industriel",
        "GEN":   "Enseignements Généraux",
    })
    with engine.begin() as c:
        c.execute(text("TRUNCATE TABLE dim_filiere CASCADE"))
    filieres.to_sql("dim_filiere", engine, if_exists="append", index=False)
    logger.info(f"dim_filiere: {len(filieres)} lignes.")

    # dim_student
    students = pd.read_sql(
        "SELECT id as student_id, nom, prenom, sexe, date_naissance, email, filiere_id, annee_entree, ville_origine FROM students",
        engine
    )
    with engine.begin() as c:
        c.execute(text("TRUNCATE TABLE dim_student CASCADE"))
    students.to_sql("dim_student", engine, if_exists="append", index=False)
    logger.info(f"dim_student: {len(students)} lignes.")

    # dim_course
    courses = pd.read_sql(
        "SELECT id as course_id, nom, filiere_id, semestre as semestre_label, credits FROM courses",
        engine
    )
    with engine.begin() as c:
        c.execute(text("TRUNCATE TABLE dim_course CASCADE"))
    courses.to_sql("dim_course", engine, if_exists="append", index=False)
    logger.info(f"dim_course: {len(courses)} lignes.")

    # dim_teacher
    teachers = pd.read_sql(
        "SELECT id as teacher_id, nom, prenom, departement, grade, salaire FROM teachers",
        engine
    )
    with engine.begin() as c:
        c.execute(text("TRUNCATE TABLE dim_teacher CASCADE"))
    teachers.to_sql("dim_teacher", engine, if_exists="append", index=False)
    logger.info(f"dim_teacher: {len(teachers)} lignes.")

    # dim_room
    rooms = pd.read_sql(
        "SELECT id as room_id, nom, capacite, type FROM rooms",
        engine
    )
    with engine.begin() as c:
        c.execute(text("TRUNCATE TABLE dim_room CASCADE"))
    rooms.to_sql("dim_room", engine, if_exists="append", index=False)
    logger.info(f"dim_room: {len(rooms)} lignes.")

    # dim_department
    depts = pd.read_sql("SELECT DISTINCT departement as nom FROM finance WHERE departement IS NOT NULL", engine)
    with engine.begin() as c:
        c.execute(text("TRUNCATE TABLE dim_department RESTART IDENTITY CASCADE"))
    depts.to_sql("dim_department", engine, if_exists="append", index=False)
    logger.info(f"dim_department: {len(depts)} lignes.")


def populate_facts(engine):
    time_df = pd.read_sql("SELECT time_id, annee_universitaire, semestre FROM dim_time", engine)
    time_map = {(r.annee_universitaire, r.semestre): r.time_id for r in time_df.itertuples()}

    # fact_grades
    grades = pd.read_sql(
        "SELECT student_id, course_id, note, semestre, annee_universitaire FROM grades",
        engine
    )
    grades["time_id"] = grades.apply(
        lambda r: time_map.get((r["annee_universitaire"], int(r["semestre"])), None), axis=1
    )
    grades = grades.dropna(subset=["time_id"])
    grades["time_id"] = grades["time_id"].astype(int)
    fact_g = grades[["student_id", "course_id", "time_id", "note"]].copy()
    with engine.begin() as c:
        c.execute(text("TRUNCATE TABLE fact_grades RESTART IDENTITY CASCADE"))
    fact_g.to_sql("fact_grades", engine, if_exists="append", index=False, chunksize=1000)
    logger.info(f"fact_grades: {len(fact_g)} lignes.")

    # fact_enrollments
    enr = pd.read_sql(
        "SELECT student_id, filiere_id, annee_universitaire, statut, annee_cursus FROM enrollments WHERE statut IS NOT NULL",
        engine
    )
    enr["semestre"] = 1  # proxy
    enr["time_id"] = enr.apply(
        lambda r: time_map.get((r["annee_universitaire"], 1), None), axis=1
    )
    enr = enr.dropna(subset=["time_id"])
    enr["time_id"] = enr["time_id"].astype(int)
    fact_e = enr[["student_id", "filiere_id", "time_id", "statut", "annee_cursus"]].copy()
    with engine.begin() as c:
        c.execute(text("TRUNCATE TABLE fact_enrollments RESTART IDENTITY CASCADE"))
    fact_e.to_sql("fact_enrollments", engine, if_exists="append", index=False, chunksize=500)
    logger.info(f"fact_enrollments: {len(fact_e)} lignes.")

    # fact_finance
    fin = pd.read_sql(
        "SELECT f.*, d.department_id FROM finance f JOIN dim_department d ON f.departement = d.nom",
        engine
    )
    fin["semestre"] = 1
    fin["time_id"] = fin.apply(
        lambda r: time_map.get((r["annee_universitaire"], 1), None), axis=1
    )
    fin = fin.dropna(subset=["time_id"])
    fin["time_id"] = fin["time_id"].astype(int)
    fin["anomalie_budget"] = fin.get("anomalie_budget", False)
    fact_f = fin[["department_id", "time_id", "budget", "depenses", "taux_execution_pct", "anomalie_budget"]].copy()
    fact_f.rename(columns={"taux_execution_pct": "taux_execution"}, inplace=True)
    with engine.begin() as c:
        c.execute(text("TRUNCATE TABLE fact_finance RESTART IDENTITY CASCADE"))
    fact_f.to_sql("fact_finance", engine, if_exists="append", index=False)
    logger.info(f"fact_finance: {len(fact_f)} lignes.")

    # fact_teaching
    teach = pd.read_sql("SELECT teacher_id, course_id, heures FROM teaching", engine)
    with engine.begin() as c:
        c.execute(text("TRUNCATE TABLE fact_teaching RESTART IDENTITY CASCADE"))
    teach.to_sql("fact_teaching", engine, if_exists="append", index=False)
    logger.info(f"fact_teaching: {len(teach)} lignes.")

    # fact_schedule
    sched = pd.read_sql(
        "SELECT course_id, room_id, date, heure, annee_universitaire FROM schedule",
        engine
    )
    sched["time_id"] = sched.apply(
        lambda r: time_map.get((r["annee_universitaire"], 1), None), axis=1
    )
    sched = sched.dropna(subset=["time_id"])
    sched["time_id"] = sched["time_id"].astype(int)
    fact_s = sched[["course_id", "room_id", "time_id", "date", "heure"]].copy()
    fact_s.rename(columns={"date": "date_session"}, inplace=True)
    with engine.begin() as c:
        c.execute(text("TRUNCATE TABLE fact_schedule RESTART IDENTITY CASCADE"))
    fact_s.to_sql("fact_schedule", engine, if_exists="append", index=False)
    logger.info(f"fact_schedule: {len(fact_s)} lignes.")


def build_warehouse():
    engine = get_engine()
    logger.info("🏗  Construction du Data Warehouse ENSA Kénitra...")
    apply_schema(engine)
    populate_dim_time(engine)
    populate_dimensions(engine)
    populate_facts(engine)
    logger.info("✅ Data Warehouse construit avec succès.")


if __name__ == "__main__":
    build_warehouse()
