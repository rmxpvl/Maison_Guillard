import os

import pytest
from app.services.auth_service import JWTError

from app.services import auth_service


def test_jeton_admin_porte_le_role_admin():
    jeton = auth_service.creer_jeton(1, "admin@test.com", "admin", heures=1)

    assert auth_service.verify_token(jeton, role="admin")["role"] == "admin"


def test_un_jeton_ne_sert_que_pour_son_role():
    jeton_client = auth_service.creer_jeton(7, "jeanne@test.com", "client", heures=1)
    jeton_admin = auth_service.creer_jeton(1, "admin@test.com", "admin", heures=1)

    with pytest.raises(JWTError):
        auth_service.verify_token(jeton_client, role="admin")
    with pytest.raises(JWTError):
        auth_service.verify_token(jeton_admin, role="client")
    assert auth_service.verify_token(jeton_client, role="client")["sub"] == "7"


def test_un_ancien_jeton_sans_role_n_est_plus_accepte():
    from datetime import datetime, timedelta, timezone

    import jwt

    ancien = jwt.encode(
        {"sub": 1, "email": "admin@test.com", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        os.environ["JWT_SECRET"], algorithm="HS256",
    )

    with pytest.raises(JWTError):
        auth_service.verify_token(ancien, role="admin")
