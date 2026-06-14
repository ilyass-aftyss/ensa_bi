"""
Teachers router — /teachers/me endpoints (role : enseignant).
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import Teacher, Teaching, Course, Grade, Student, Filiere
from app.security import require_role, require_direction_or_admin, get_current_user

router = APIRouter(prefix="/teachers", tags=["Enseignants"])

require_enseignant_or_admin = require_role("administrateur", "direction", "enseignant")


@router.get("/me", summary="Profil de l'enseignant connecte")
def teacher_me(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("enseignant", "administrateur")),
):
    teacher_id = current_user.get("teacher_id")
    if not teacher_id:
        raise HTTPException(status_code=400, detail="Aucun profil enseignant lie a ce compte")
    t = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Enseignant introuvable")
    return {
        "id": t.id,
        "nom": t.nom,
        "prenom": t.prenom,
        "departement": t.departement,
        "grade": t.grade,
    }


@router.get("/me/courses", summary="Cours de l'enseignant connecte")
def teacher_my_courses(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("enseignant", "administrateur")),
):
    teacher_id = current_user.get("teacher_id")
    if not teacher_id:
        raise HTTPException(status_code=400, detail="Aucun profil enseignant lie a ce compte")

    rows = (
        db.query(
            Course.id,
            Course.nom,
            Course.semestre,
            Course.credits,
            Filiere.nom.label("filiere"),
            Teaching.heures,
        )
        .join(Teaching, Teaching.course_id == Course.id)
        .join(Filiere, Filiere.id == Course.filiere_id, isouter=True)
        .filter(Teaching.teacher_id == teacher_id)
        .all()
    )

    results = []
    for r in rows:
        nb_students = (
            db.query(func.count(func.distinct(Grade.student_id)))
            .filter(Grade.course_id == r.id)
            .scalar() or 0
        )
        avg = (
            db.query(func.avg(Grade.note))
            .filter(Grade.course_id == r.id, Grade.note.isnot(None))
            .scalar()
        )
        results.append({
            "course_id":  r.id,
            "nom":        r.nom,
            "semestre":   r.semestre,
            "credits":    r.credits,
            "filiere":    r.filiere,
            "heures":     r.heures,
            "nb_etudiants": nb_students,
            "moyenne":    round(float(avg), 2) if avg else None,
        })
    return results


@router.get("/me/students-performance", summary="Performance des etudiants de l'enseignant")
def teacher_students_performance(
    annee_universitaire: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("enseignant", "administrateur")),
):
    teacher_id = current_user.get("teacher_id")
    if not teacher_id:
        raise HTTPException(status_code=400, detail="Aucun profil enseignant lie a ce compte")

    course_ids = [
        row[0]
        for row in db.query(Teaching.course_id).filter(Teaching.teacher_id == teacher_id).all()
    ]
    if not course_ids:
        return []

    q = (
        db.query(
            Course.nom.label("cours"),
            func.count(Grade.id).label("nb_notes"),
            func.avg(Grade.note).label("moyenne"),
            func.sum(
                __import__("sqlalchemy").case((Grade.note >= 10, 1), else_=0)
            ).label("nb_reussite"),
        )
        .join(Grade, Grade.course_id == Course.id)
        .filter(Grade.course_id.in_(course_ids), Grade.note.isnot(None))
    )
    if annee_universitaire:
        q = q.filter(Grade.annee_universitaire == annee_universitaire)
    rows = q.group_by(Course.id, Course.nom).order_by(Course.nom).all()

    return [
        {
            "cours":            r.cours,
            "nb_notes":         r.nb_notes,
            "moyenne":          round(float(r.moyenne or 0), 2),
            "taux_reussite_pct": round(r.nb_reussite / r.nb_notes * 100, 1) if r.nb_notes else 0,
        }
        for r in rows
    ]


@router.get("/", summary="Liste des enseignants (direction/admin)")
def list_teachers(
    db: Session = Depends(get_db),
    _user: dict = Depends(require_direction_or_admin),
):
    rows = db.query(Teacher).order_by(Teacher.departement, Teacher.nom).all()
    return [
        {
            "id": t.id,
            "nom": t.nom,
            "prenom": t.prenom,
            "departement": t.departement,
            "grade": t.grade,
        }
        for t in rows
    ]
