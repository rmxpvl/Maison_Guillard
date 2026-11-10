from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.client import Client
from app.services import auth_service

bearer = HTTPBearer(auto_error=False, description="Jeton obtenu via POST /api/clients/connexion")


def require_client(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> Client:
    """The logged-in customer. An admin token (or any token of another role) is refused."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        claims = auth_service.verify_token(credentials.credentials, role="client")
        client = db.get(Client, int(claims["sub"]))
    except Exception:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if client is None or client.email_verifie_at is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return client
