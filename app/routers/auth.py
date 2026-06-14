"""
Auth router — /auth/token et /auth/me.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.security import (
    authenticate_user, create_access_token, get_current_user,
    Token, ROLE_LABELS,
)

router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post("/token", response_model=Token, summary="Obtenir un token JWT")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token({
        "sub": user["username"],
        "role": user["role"],
        "student_id": user.get("student_id"),
        "teacher_id": user.get("teacher_id"),
    })
    return Token(
        access_token=token,
        token_type="bearer",
        role=user["role"],
        full_name=user["full_name"],
        username=user["username"],
    )


@router.get("/me", summary="Profil de l'utilisateur connecte")
async def me(current_user: dict = Depends(get_current_user)):
    role = current_user["role"]
    return {
        "username":   current_user["username"],
        "full_name":  current_user["full_name"],
        "role":       role,
        "role_label": ROLE_LABELS.get(role, role),
        "student_id": current_user.get("student_id"),
        "teacher_id": current_user.get("teacher_id"),
        "permissions": {
            "can_see_finance":    role in ("administrateur", "direction"),
            "can_see_rh":         role in ("administrateur", "direction"),
            "can_see_global_kpi": role in ("administrateur", "direction"),
            "can_see_own_data":   role == "etudiant",
            "can_see_courses":    role in ("administrateur", "direction", "enseignant"),
            "is_admin":           role == "administrateur",
        },
    }
