import os
from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.models.admin import Admin

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TOKEN_EXPIRY_HOURS = 8
JWT_ALGORITHM = "HS256"


class InvalidCredentialsError(Exception):
    """Raised when login is attempted with an unknown email or wrong password."""


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def login(db: Session, email: str, password: str) -> str:
    admin = db.query(Admin).filter(Admin.email == email).first()
    if admin is None:
        raise InvalidCredentialsError()

    if not verify_password(password, admin.password_hash):
        raise InvalidCredentialsError()

    return creer_jeton(admin.id, admin.email, "admin", TOKEN_EXPIRY_HOURS)


def creer_jeton(sub: int, email: str, role: str, heures: int) -> str:
    """Signed token. `role` ("admin" or "client") keeps the two kinds of account apart: a token
    is only accepted where its role is expected."""
    payload = {
        "sub": sub,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=heures),
    }
    return jwt.encode(payload, os.environ["JWT_SECRET"], algorithm=JWT_ALGORITHM)


def verify_token(token: str, role: str) -> dict:
    secret = os.environ["JWT_SECRET"]
    try:
        claims = jwt.decode(
            token, secret, algorithms=[JWT_ALGORITHM], options={"verify_sub": False}
        )
    except JWTError as exc:
        raise JWTError("Invalid or expired token") from exc
    if claims.get("role") != role:  # also rejects tokens issued before roles existed
        raise JWTError("Wrong token role")
    return claims