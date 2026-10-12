from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["Authentification"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    try:
        token = auth_service.login(db, payload.email, payload.motDePasse)
    except auth_service.InvalidCredentialsError:
        raise HTTPException(status_code=401, detail="Identifiants invalides")
    return TokenResponse(token=token)