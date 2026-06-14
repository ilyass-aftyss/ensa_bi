"""
Students router — /students endpoints avec controle d'acces par role.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import Student, Filiere, Enrollment, Grade, Course, Schedule, Room
from app.security import require_role, require_direction_or_admin, require_staff
from pydantic import BaseModel
from datetime import date

router = APIRouter(prefix="/students", tags=["Etudiants"])


class StudentOut(BaseModel):
    id: int
    nom: str
    prenom: str
    sexe: Optional[str]
    email: Optional[str]
    filiere_id: Optional[int]
    annee_cursus: Optional[int]
    annee_entree: Optional[int]
    ville_origine: Optional[str]
    model_config = {"from_attributes": True}


# ── Endpoints "Mon Espace" (role etudiant) ───────────────────────────────────

@router.get("/me", summary="Profil de l'etudiant connecte")
def student_me(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("etudiant", "administrateur")),
):
    sid = current_user.get("student_id")
    if not sid:
        raise HTTPException(400, "Aucun profil etudiant lie a ce compte")
    s = db.query(Student).filter(Student.id == sid).first()
    if not s:
        raise HTTPException(404, "Etudiant introuvable")
    filiere = db.query(Filiere).filter(Filiere.id == s.filiere_id).first()
    return {
        "id":           s.id,
        "nom":          s.nom,
        "prenom":       s.prenom,
        "email":        s.email,
        "sexe":         s.sexe,
        "date_naissance": str(s.date_naissance) if s.date_naissance else None,
        "filiere":      filiere.nom if filiere else None,
        "filiere_id":   s.filiere_id,
        "annee_cursus": s.annee_cursus,
        "annee_entree": s.annee_entree,
        "ville_origine": s.ville_origine,
    }


@router.get("/me/grades", summary="Notes de l'etudiant connecte")
def student_my_grades(
    annee_universitaire: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("etudiant", "administrateur")),
):
    sid = current_user.get("student_id")
    if not sid:
        raise HTTPException(400, "Aucun profil etudiant lie a ce compte")
    q = (
        db.query(Grade, Course.nom.label("cours"))
        .join(Course, Course.id == Grade.course_id)
        .filter(Grade.student_id == sid, Grade.note.isnot(None))
    )
    if annee_universitaire:
        q = q.filter(Grade.annee_universitaire == annee_universitaire)
    rows = q.order_by(Grade.annee_universitaire, Grade.semestre, Course.nom).all()

    results = []
    for g, cours in rows:
        results.append({
            "cours":               cours,
            "note":                float(g.note),
            "semestre":            g.semestre,
            "annee_universitaire": g.annee_universitaire,
            "mention":             _mention(float(g.note)),
        })
    return results


@router.get("/me/schedule", summary="Emploi du temps de l'etudiant connecte")
def student_my_schedule(
    annee_universitaire: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("etudiant", "administrateur")),
):
    sid = current_user.get("student_id")
    if not sid:
        raise HTTPException(400, "Aucun profil etudiant lie a ce compte")
    student = db.query(Student).filter(Student.id == sid).first()
    if not student or not student.filiere_id:
        return []

    q = (
        db.query(
            Schedule.date,
            Schedule.heure,
            Schedule.annee_universitaire,
            Course.nom.label("cours"),
            Course.semestre.label("semestre_cours"),
            Room.nom.label("salle"),
            Room.type.label("type_salle"),
        )
        .join(Course, Course.id == Schedule.course_id)
        .join(Room, Room.id == Schedule.room_id, isouter=True)
        .filter(Course.filiere_id == student.filiere_id)
    )
    if annee_universitaire:
        q = q.filter(Schedule.annee_universitaire == annee_universitaire)
    rows = q.order_by(Schedule.date, Schedule.heure).all()

    return [
        {
            "date":  str(r.date) if r.date else None,
            "heure": r.heure,
            "annee_universitaire": r.annee_universitaire,
            "cours": r.cours,
            "semestre": r.semestre_cours,
            "salle": r.salle,
            "type_salle": r.type_salle,
        }
        for r in rows
    ]


@router.get("/me/enrollments", summary="Historique des inscriptions de l'etudiant")
def student_my_enrollments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("etudiant", "administrateur")),
):
    sid = current_user.get("student_id")
    if not sid:
        raise HTTPException(400, "Aucun profil etudiant lie a ce compte")
    rows = (
        db.query(Enrollment, Filiere.nom.label("filiere"))
        .join(Filiere, Filiere.id == Enrollment.filiere_id, isouter=True)
        .filter(Enrollment.student_id == sid)
        .order_by(Enrollment.annee_universitaire)
        .all()
    )
    return [
        {
            "annee_universitaire": e.annee_universitaire,
            "filiere":             f,
            "statut":              e.statut,
            "annee_cursus":        e.annee_cursus,
        }
        for e, f in rows
    ]


# ── Endpoints staff (direction/admin/enseignant) ──────────────────────────────

@router.get("/", summary="Liste des etudiants (staff uniquement)")
def list_students(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    filiere_id: Optional[int] = None,
    annee: Optional[int] = None,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_staff),
):
    q = db.query(Student)
    if filiere_id:
        q = q.filter(Student.filiere_id == filiere_id)
    if annee:
        q = q.filter(Student.annee_cursus == annee)
    total = q.count()
    students = q.offset(skip).limit(limit).all()
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [StudentOut.model_validate(s) for s in students],
    }


@router.get("/count", summary="Nombre total d'etudiants")
def count_students(
    filiere_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_staff),
):
    q = db.query(func.count(Student.id))
    if filiere_id:
        q = q.filter(Student.filiere_id == filiere_id)
    return {"total": q.scalar()}


@router.get("/by-filiere", summary="Repartition etudiants par filiere")
def students_by_filiere(
    db: Session = Depends(get_db),
    _user: dict = Depends(require_staff),
):
    rows = (
        db.query(Filiere.nom, func.count(Student.id).label("count"))
        .join(Student, Student.filiere_id == Filiere.id, isouter=True)
        .group_by(Filiere.nom)
        .all()
    )
    return [{"filiere": r[0], "count": r[1]} for r in rows]


@router.get("/evolution", summary="Evolution inscriptions par annee")
def students_evolution(
    db: Session = Depends(get_db),
    _user: dict = Depends(require_staff),
):
    rows = (
        db.query(
            Enrollment.annee_universitaire,
            Filiere.nom,
            func.count(Enrollment.id).label("count"),
        )
        .join(Filiere, Filiere.id == Enrollment.filiere_id, isouter=True)
        .filter(Enrollment.statut == "inscrit")
        .group_by(Enrollment.annee_universitaire, Filiere.nom)
        .order_by(Enrollment.annee_universitaire)
        .all()
    )
    return [{"annee": r[0], "filiere": r[1], "count": r[2]} for r in rows]


@router.get("/{student_id}", summary="Detail d'un etudiant (staff)")
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_staff),
):
    s = db.query(Student).filter(Student.id == student_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Etudiant introuvable")
    return StudentOut.model_validate(s)


def _mention(note: float) -> str:
    if note >= 16: return "Tres bien"
    if note >= 14: return "Bien"
    if note >= 12: return "Assez bien"
    if note >= 10: return "Passable"
    return "Insuffisant"
