import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.admin import Admin
from app.services import auth_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def seed_admin():
    db = SessionLocal()
    db.query(Admin).delete()
    db.commit()
    admin = Admin(
        email="admin@test.com",
        password_hash=auth_service.hash_password("test-password-123"),
    )
    db.add(admin)
    db.commit()
    yield
    db.query(Admin).delete()
    db.commit()
    db.close()


def test_login_returns_200_and_token_for_valid_credentials():
    res = client.post(
        "/api/auth/login",
        json={"email": "admin@test.com", "motDePasse": "test-password-123"},
    )
    assert res.status_code == 200
    assert "token" in res.json()


def test_login_returns_401_for_wrong_password():
    res = client.post(
        "/api/auth/login",
        json={"email": "admin@test.com", "motDePasse": "wrong-password"},
    )
    assert res.status_code == 401


def test_login_returns_401_for_unknown_email():
    res = client.post(
        "/api/auth/login",
        json={"email": "nobody@test.com", "motDePasse": "whatever"},
    )
    assert res.status_code == 401


def test_login_returns_422_when_motdepasse_missing():
    res = client.post("/api/auth/login", json={"email": "admin@test.com"})
    assert res.status_code == 422


def test_protected_route_rejects_missing_authorization_header():
    res = client.get("/api/health/protected-check")
    assert res.status_code == 401


def test_protected_route_accepts_valid_token():
    login_res = client.post(
        "/api/auth/login",
        json={"email": "admin@test.com", "motDePasse": "test-password-123"},
    )
    token = login_res.json()["token"]

    res = client.get(
        "/api/health/protected-check",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200