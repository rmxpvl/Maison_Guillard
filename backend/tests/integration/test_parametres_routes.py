import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.admin import Admin
from app.models.parametre import Parametre
from app.services import auth_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()
    db.query(Parametre).delete()
    db.query(Admin).delete()
    db.commit()
    yield db
    db.query(Parametre).delete()
    db.query(Admin).delete()
    db.commit()
    db.close()


def _entetes(db):
    db.add(Admin(email="admin@test.com", password_hash=auth_service.hash_password("test-password-123")))
    db.commit()
    token = auth_service.login(db, "admin@test.com", "test-password-123")
    return {"Authorization": f"Bearer {token}"}


def test_email_commande_desactive_par_defaut(clean_db):
    res = client.get("/api/parametres", headers=_entetes(clean_db))

    assert res.status_code == 200
    assert res.json() == {"email_commande_actif": False}


def test_admin_active_puis_relit_le_reglage(clean_db):
    entetes = _entetes(clean_db)

    res = client.put("/api/parametres", json={"email_commande_actif": True}, headers=entetes)
    assert res.status_code == 200

    assert client.get("/api/parametres", headers=entetes).json() == {"email_commande_actif": True}
    assert clean_db.query(Parametre).count() == 1  # still a single row
