from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.services import auth_service, limiteur

router = APIRouter(prefix="/api/auth", tags=["Authentification"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Se connecter (administrateur)",
    responses={
        401: {"description": "E-mail ou mot de passe incorrect"},
        429: {"description": "Trop de tentatives"},
    },
    dependencies=[limiteur.limite_ip("connexion-admin", 10, 900)],
)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    # Also per account: guessing one password from many addresses is stopped as well.
    limiteur.verifier("connexion-admin-compte", payload.email.strip().lower(), 10, 900)
    try:
        token = auth_service.login(db, payload.email, payload.motDePasse)
    except auth_service.InvalidCredentialsError:
        raise HTTPException(status_code=401, detail="Identifiants invalides")
    return TokenResponse(token=token)
