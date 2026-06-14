"""
JWT authentication + RBAC — 4 rôles : administrateur, direction, enseignant, etudiant.
Les credentials sont stockés dans users_config.json, généré depuis la DB au premier démarrage.
"""
import os
import json
import logging
import unicodedata
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("ensa_bi.security")

SECRET_KEY = os.getenv("SECRET_KEY", "ensa-kenitra-bi-secret-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))

USERS_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "users_config.json"
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

USERS_DB: dict[str, dict] = {}

ROLE_LABELS = {
    "administrateur": "Administrateur",
    "direction":      "Direction",
    "enseignant":     "Enseignant",
    "etudiant":       "Etudiant",
}

ROLE_ICONS = {
    "administrateur": "Shield",
    "direction":      "Target",
    "enseignant":     "Book",
    "etudiant":       "GraduationCap",
}

ROLE_PERMISSIONS: dict[str, list[str]] = {
    "administrateur": ["read", "write", "delete", "kpi_all", "finance", "hr", "admin"],
    "direction":      ["read", "kpi_all", "finance", "hr"],
    "enseignant":     ["read", "kpi_grades", "kpi_resources"],
    "etudiant":       ["read_own"],
}


def _clean(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.lower().replace(" ", "").replace("-", "").replace("'", "")


def make_teacher_username(prenom: str, nom: str) -> str:
    return f"{_clean(prenom)}.{_clean(nom)}"


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def load_users_from_config() -> bool:
    global USERS_DB
    if os.path.exists(USERS_CONFIG_PATH):
        try:
            with open(USERS_CONFIG_PATH, "r", encoding="utf-8") as f:
                USERS_DB = json.load(f)
            logger.info(f"[AUTH] {len(USERS_DB)} comptes charges depuis users_config.json")
            return True
        except Exception as e:
            logger.error(f"Erreur lecture users_config.json : {e}")
    _load_default_users()
    logger.warning("[AUTH] users_config.json introuvable - comptes par defaut charges")
    return False


def _load_default_users():
    global USERS_DB
    USERS_DB = {
        "admin": {
            "hashed_password": get_password_hash("Admin@ENSA2025"),
            "role": "administrateur",
            "full_name": "Administrateur Systeme",
            "student_id": None,
            "teacher_id": None,
        },
        "direction": {
            "hashed_password": get_password_hash("Direction@ENSA2025"),
            "role": "direction",
            "full_name": "Directeur ENSA Kenitra",
            "student_id": None,
            "teacher_id": None,
        },
    }


def save_users_to_config():
    try:
        with open(USERS_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(USERS_DB, f, ensure_ascii=False, indent=2)
        logger.info(f"[AUTH] users_config.json sauvegarde ({len(USERS_DB)} comptes)")
    except Exception as e:
        logger.error(f"Erreur sauvegarde users_config.json : {e}")


def needs_seeding() -> bool:
    """Renvoie True si aucun etudiant ni enseignant n'est encore enregistre."""
    return not any(
        u.get("role") in ("etudiant", "enseignant") for u in USERS_DB.values()
    )


def seed_users_from_db(db_session) -> tuple[int, int]:
    """
    Peuple users_config.json depuis les tables students et teachers.
    - Etudiant  : username = email,        mot de passe = Etudiant_<id>
    - Enseignant: username = prenom.nom,   mot de passe = Enseignant_<id>
    """
    global USERS_DB
    from app.models import Student, Teacher

    _load_default_users()
    new_users = dict(USERS_DB)
    count_s = count_t = 0

    try:
        for s in db_session.query(Student).all():
            if not s.email:
                continue
            uname = s.email.lower().strip()
            if uname in new_users:
                continue
            new_users[uname] = {
                "hashed_password": get_password_hash(f"Etudiant_{s.id}"),
                "role": "etudiant",
                "full_name": f"{s.prenom} {s.nom}",
                "student_id": s.id,
                "teacher_id": None,
            }
            count_s += 1
    except Exception as e:
        logger.error(f"Seeding etudiants : {e}")

    try:
        used: set[str] = set(new_users.keys())
        for t in db_session.query(Teacher).all():
            uname = make_teacher_username(t.prenom, t.nom)
            if uname in used:
                uname = f"{uname}.{t.id}"
            used.add(uname)
            new_users[uname] = {
                "hashed_password": get_password_hash(f"Enseignant_{t.id}"),
                "role": "enseignant",
                "full_name": f"{t.prenom} {t.nom}",
                "student_id": None,
                "teacher_id": t.id,
            }
            count_t += 1
    except Exception as e:
        logger.error(f"Seeding enseignants : {e}")

    USERS_DB = new_users
    save_users_to_config()
    logger.info(f"[AUTH] Seeding : {count_s} etudiants + {count_t} enseignants")
    return count_s, count_t


def authenticate_user(username: str, password: str) -> Optional[dict]:
    uname = username.lower().strip()
    user = USERS_DB.get(uname)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return {**user, "username": uname}


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None
    student_id: Optional[int] = None
    teacher_id: Optional[int] = None


class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    full_name: str
    username: str


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expire",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub", "")
        if not username:
            raise exc
        token_data = TokenData(
            username=username,
            role=payload.get("role"),
            student_id=payload.get("student_id"),
            teacher_id=payload.get("teacher_id"),
        )
    except JWTError:
        raise exc
    user = USERS_DB.get(token_data.username or "")
    if not user:
        raise exc
    return {
        **user,
        "username": token_data.username,
        "student_id": token_data.student_id,
        "teacher_id": token_data.teacher_id,
    }


def require_role(*allowed_roles: str):
    async def checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acces refuse. Roles autorises : {chr(39)}{chr(39).join(allowed_roles)}{chr(39)}",
            )
        return current_user
    return checker


require_admin              = require_role("administrateur")
require_direction_or_admin = require_role("administrateur", "direction")
require_staff              = require_role("administrateur", "direction", "enseignant")
require_any                = require_role("administrateur", "direction", "enseignant", "etudiant")
