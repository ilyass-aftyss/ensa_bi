"""
KPI router — indicateurs decisionnels avec controle d'acces par role.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.database import get_db
from app.models import Grade, Student, Enrollment, Finance, Course, Teaching, Teacher, Room, Schedule, Filiere
from app.security import require_staff, require_direction_or_admin, require_any

router = APIRouter(prefix="/kpi", tags=["KPI Decisionnels"])


@router.get("/success-rate", summary="Taux de reussite par filiere")
def success_rate(
    annee_universitaire: Optional[str] = None,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_staff),
):
    q = (
        db.query(
            Filiere.nom.label("filiere"),
            func.count(Grade.id).label("total_notes"),
            func.sum(case((Grade.note >= 10, 1), else_=0)).label("nb_reussite"),
            func.avg(Grade.note).label("moyenne"),
        )
        .join(Student, Student.id == Grade.student_id)
        .join(Filiere, Filiere.id == Student.filiere_id)
        .filter(Grade.note.isnot(None))
    )
    if annee_universitaire:
        q = q.filter(Grade.annee_universitaire == annee_universitaire)
    rows = q.group_by(Filiere.nom).all()
    results = []
    for r in rows:
        taux = round(r.nb_reussite / r.total_notes * 100, 2) if r.total_notes else 0
        results.append({
            "filiere": r.filiere,
            "taux_reussite_pct": taux,
            "moyenne_generale": round(float(r.moyenne or 0), 2),
            "total_notes": r.total_notes,
        })
    results.sort(key=lambda x: x["taux_reussite_pct"], reverse=True)
    return results


@router.get("/abandon-rate", summary="Taux d'abandon par filiere")
def abandon_rate(
    annee_universitaire: Optional[str] = None,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_staff),
):
    q = (
        db.query(
            Filiere.nom.label("filiere"),
            func.count(Enrollment.id).label("total"),
            func.sum(case((Enrollment.statut == "abandonne", 1), else_=0)).label("nb_abandon"),
        )
        .join(Filiere, Filiere.id == Enrollment.filiere_id)
        .filter(Enrollment.statut.isnot(None))
    )
    if annee_universitaire:
        q = q.filter(Enrollment.annee_universitaire == annee_universitaire)
    rows = q.group_by(Filiere.nom).all()
    results = []
    for r in rows:
        taux = round(r.nb_abandon / r.total * 100, 2) if r.total else 0
        results.append({
            "filiere": r.filiere,
            "taux_abandon_pct": taux,
            "nb_abandon": int(r.nb_abandon or 0),
            "total_inscrits": r.total,
        })
    return results


@router.get("/avg-grade", summary="Moyenne generale globale et par filiere")
def avg_grade(
    annee_universitaire: Optional[str] = None,
    filiere_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_staff),
):
    q = db.query(func.avg(Grade.note)).filter(Grade.note.isnot(None))
    if annee_universitaire:
        q = q.filter(Grade.annee_universitaire == annee_universitaire)
    if filiere_id:
        q = q.join(Student, Student.id == Grade.student_id).filter(Student.filiere_id == filiere_id)
    global_avg = round(float(q.scalar() or 0), 2)

    by_filiere_q = (
        db.query(Filiere.nom, func.avg(Grade.note).label("avg"))
        .join(Student, Student.id == Grade.student_id)
        .join(Filiere, Filiere.id == Student.filiere_id)
        .filter(Grade.note.isnot(None))
    )
    if annee_universitaire:
        by_filiere_q = by_filiere_q.filter(Grade.annee_universitaire == annee_universitaire)
    by_filiere = [
        {"filiere": r[0], "moyenne": round(float(r[1] or 0), 2)}
        for r in by_filiere_q.group_by(Filiere.nom).all()
    ]
    return {"moyenne_globale": global_avg, "par_filiere": by_filiere}


@router.get("/budget-usage", summary="Taux d'execution budgetaire (direction/admin)")
def budget_usage(
    annee_universitaire: Optional[str] = None,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_direction_or_admin),
):
    q = db.query(Finance.departement, Finance.annee_universitaire, Finance.budget,
                 Finance.depenses, Finance.taux_execution_pct)
    if annee_universitaire:
        q = q.filter(Finance.annee_universitaire == annee_universitaire)
    rows = q.order_by(Finance.annee_universitaire, Finance.departement).all()
    total_budget = sum(float(r.budget or 0) for r in rows)
    total_dep = sum(float(r.depenses or 0) for r in rows)
    taux_global = round(total_dep / total_budget * 100, 2) if total_budget else 0
    return {
        "taux_execution_global_pct": taux_global,
        "total_budget": round(total_budget, 2),
        "total_depenses": round(total_dep, 2),
        "par_departement": [
            {
                "departement": r.departement,
                "annee": r.annee_universitaire,
                "budget": float(r.budget or 0),
                "depenses": float(r.depenses or 0),
                "taux_pct": float(r.taux_execution_pct or 0),
            }
            for r in rows
        ],
    }


@router.get("/top-filieres", summary="Classement des filieres par performance")
def top_filieres(
    annee_universitaire: Optional[str] = None,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_staff),
):
    q = (
        db.query(
            Filiere.nom.label("filiere"),
            func.avg(Grade.note).label("moyenne"),
            func.count(func.distinct(Student.id)).label("nb_etudiants"),
        )
        .join(Student, Student.id == Grade.student_id)
        .join(Filiere, Filiere.id == Student.filiere_id)
        .filter(Grade.note.isnot(None))
    )
    if annee_universitaire:
        q = q.filter(Grade.annee_universitaire == annee_universitaire)
    rows = q.group_by(Filiere.nom).order_by(func.avg(Grade.note).desc()).all()
    return [
        {
            "rank": i + 1,
            "filiere": r.filiere,
            "moyenne": round(float(r.moyenne or 0), 2),
            "nb_etudiants": r.nb_etudiants,
        }
        for i, r in enumerate(rows)
    ]


@router.get("/teacher-workload", summary="Charge des enseignants")
def teacher_workload(
    db: Session = Depends(get_db),
    _user: dict = Depends(require_staff),
):
    rows = (
        db.query(
            Teacher.nom, Teacher.prenom, Teacher.departement,
            func.sum(Teaching.heures).label("total_heures"),
            func.count(Teaching.course_id).label("nb_cours"),
        )
        .join(Teaching, Teaching.teacher_id == Teacher.id)
        .group_by(Teacher.id, Teacher.nom, Teacher.prenom, Teacher.departement)
        .order_by(func.sum(Teaching.heures).desc())
        .all()
    )
    return [
        {
            "enseignant": f"{r.prenom} {r.nom}",
            "departement": r.departement,
            "total_heures": int(r.total_heures or 0),
            "nb_cours": r.nb_cours,
        }
        for r in rows
    ]


@router.get("/room-occupancy", summary="Taux d'occupation des salles")
def room_occupancy(
    annee_universitaire: Optional[str] = None,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_staff),
):
    q = (
        db.query(
            Room.nom, Room.type, Room.capacite,
            func.count(Schedule.id).label("nb_sessions"),
        )
        .join(Schedule, Schedule.room_id == Room.id, isouter=True)
    )
    if annee_universitaire:
        q = q.filter(Schedule.annee_universitaire == annee_universitaire)
    rows = q.group_by(Room.id, Room.nom, Room.type, Room.capacite).all()
    max_sessions = max((r.nb_sessions for r in rows), default=1)
    return [
        {
            "salle": r.nom,
            "type": r.type,
            "capacite": r.capacite,
            "nb_sessions": r.nb_sessions,
            "taux_occupation_pct": round(r.nb_sessions / max_sessions * 100, 1),
        }
        for r in rows
    ]


@router.get("/enrollments-summary", summary="Resume inscriptions / abandons / diplomes")
def enrollments_summary(
    annee_universitaire: Optional[str] = None,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_staff),
):
    q = db.query(Enrollment.statut, func.count(Enrollment.id).label("count")).filter(
        Enrollment.statut.isnot(None)
    )
    if annee_universitaire:
        q = q.filter(Enrollment.annee_universitaire == annee_universitaire)
    rows = q.group_by(Enrollment.statut).all()
    return {r.statut: r.count for r in rows}


@router.get("/dashboard-overview", summary="Vue globale pour le dashboard")
def dashboard_overview(
    annee_universitaire: str = "2024-2025",
    db: Session = Depends(get_db),
    _user: dict = Depends(require_staff),
):
    total_students = db.query(func.count(Student.id)).scalar() or 0
    grades_q = db.query(func.avg(Grade.note)).filter(
        Grade.note.isnot(None), Grade.annee_universitaire == annee_universitaire
    )
    global_avg = round(float(grades_q.scalar() or 0), 2)
    all_notes = db.query(Grade.note).filter(
        Grade.note.isnot(None), Grade.annee_universitaire == annee_universitaire
    ).all()
    total_n = len(all_notes)
    taux_reussite = round(sum(1 for (n,) in all_notes if n >= 10) / total_n * 100, 2) if total_n else 0
    enr_total = db.query(func.count(Enrollment.id)).filter(
        Enrollment.statut.isnot(None), Enrollment.annee_universitaire == annee_universitaire
    ).scalar() or 1
    enr_abandon = db.query(func.count(Enrollment.id)).filter(
        Enrollment.statut == "abandonne", Enrollment.annee_universitaire == annee_universitaire
    ).scalar() or 0
    taux_abandon = round(enr_abandon / enr_total * 100, 2)
    finance_rows = db.query(Finance).filter(Finance.annee_universitaire == annee_universitaire).all()
    total_budget = sum(float(r.budget or 0) for r in finance_rows)
    total_dep = sum(float(r.depenses or 0) for r in finance_rows)
    taux_budget = round(total_dep / total_budget * 100, 2) if total_budget else 0
    return {
        "annee_universitaire": annee_universitaire,
        "total_etudiants": total_students,
        "taux_reussite_global_pct": taux_reussite,
        "taux_abandon_global_pct": taux_abandon,
        "moyenne_generale": global_avg,
        "taux_execution_budgetaire_pct": taux_budget,
        "total_budget": round(total_budget, 2),
        "total_depenses": round(total_dep, 2),
        "etl_status": "actif",
        "dw_status": "synchronise",
    }
