import os
from unittest.mock import MagicMock
import pytest

os.environ.setdefault("JWT_SECRET", "test-secret")

from app.services import auth_service


def test_hash_and_verify_password_roundtrip():
    hashed = auth_service.hash_password("correct horse battery staple")
    assert hashed != "correct horse battery staple"
    assert auth_service.verify_password("correct horse battery staple", hashed) is True


def test_verify_password_rejects_wrong_password():
    hashed = auth_service.hash_password("right-password")
    assert auth_service.verify_password("wrong-password", hashed) is False


def _fake_admin(id_=1, email="admin@test.com", password="good-password"):
    admin = MagicMock()
    admin.id = id_
    admin.email = email
    admin.password_hash = auth_service.hash_password(password)
    return admin


def test_login_returns_token_for_valid_credentials():
    admin = _fake_admin()
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = admin

    token = auth_service.login(db, "admin@test.com", "good-password")

    assert isinstance(token, str)
    assert len(token) > 0


def test_login_raises_for_unknown_email():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(auth_service.InvalidCredentialsError):
        auth_service.login(db, "nobody@test.com", "whatever")


def test_login_raises_for_wrong_password():
    admin = _fake_admin(password="good-password")
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = admin

    with pytest.raises(auth_service.InvalidCredentialsError):
        auth_service.login(db, "admin@test.com", "bad-password")


def test_verify_token_decodes_a_token_from_login():
    admin = _fake_admin(id_=42, email="admin@test.com")
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = admin

    token = auth_service.login(db, "admin@test.com", "good-password")
    decoded = auth_service.verify_token(token, role="admin")

    assert decoded["sub"] == 42
    assert decoded["email"] == "admin@test.com"


def test_verify_token_raises_on_garbage_token():
    with pytest.raises(Exception):
        auth_service.verify_token("not-a-real-token", role="admin")