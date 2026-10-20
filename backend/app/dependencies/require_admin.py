from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.services import auth_service

# Declares the "Bearer token" security scheme: Swagger shows an Authorize button.
# auto_error=False: we raise our own 401 instead of FastAPI's default error.
bearer = HTTPBearer(auto_error=False, description="Jeton obtenu via POST /api/auth/login")

def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        return auth_service.verify_token(credentials.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Unauthorized")