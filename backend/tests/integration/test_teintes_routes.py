import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.admin import Admin
from app.models.categorie import Categorie, Univers
from app.models.produit import Produit
from app.models.teinte import Teinte
from app.services import auth_service

client = TestClient(app)
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 20


def _headers(db):
    db.query(Admin).delete()
    db.commit()
    db.add(Admin(email="admin@test.com", password_hash=auth_service.hash_password("test-password-123")))
    db.commit()
    return {"Authorization": f"Bearer {auth_service.login(db, 'admin@test.com', 'test-password-123')}"}


def _teinte(db, nom="Naturel", ordre=0, active=True):
    teinte = Teinte(nom=nom, image_url="http://x/y.png", ordre=ordre, active=active)
    db.add(teinte)
    db.commit()
    db.refresh(teinte)
    return teinte


def _produit_payload(db, **extra):
    categorie = db.query(Categorie).first()
    if categorie is None:
        categorie = Categorie(nom="Tables", slug="tables", univers=Univers.meubles)
        db.add(categorie)
        db.commit()
        db.refresh(categorie)
    return {
        "nom": "Table", "description": "Chêne", "categorie_id": categorie.id,
        "prix": "100.00", "dimensions": "1x1", **extra,
    }


@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()

    def vider():
        db.query(Produit).delete()
        db.query(Teinte).delete()
        db.query(Categorie).delete()
        db.query(Admin).delete()
        db.commit()

    vider()
    yield db
    vider()
    db.close()


def test_create_teinte_avec_image(clean_db):
    res = client.post(
        "/api/teintes", data={"nom": "Charcoal", "ordre": "2"},
        files={"fichier": ("c.png", PNG, "image/png")}, headers=_headers(clean_db),
    )

    assert res.status_code == 201
    body = res.json()
    assert body["nom"] == "Charcoal" and body["ordre"] == 2 and body["active"] is True
    assert "/uploads/" in body["image_url"]


def test_list_teintes_triees_par_ordre(clean_db):
    _teinte(clean_db, "B", ordre=2)
    _teinte(clean_db, "A", ordre=1)

    res = client.get("/api/teintes", headers=_headers(clean_db))

    assert [t["nom"] for t in res.json()] == ["A", "B"]


def test_update_teinte_desactive(clean_db):
    teinte = _teinte(clean_db)

    res = client.put(f"/api/teintes/{teinte.id}", json={"active": False}, headers=_headers(clean_db))

    assert res.status_code == 200
    assert res.json()["active"] is False and res.json()["nom"] == "Naturel"


def test_update_teinte_404(clean_db):
    assert client.put("/api/teintes/999999", json={"active": False}, headers=_headers(clean_db)).status_code == 404


def test_replace_image_teinte(clean_db):
    teinte = _teinte(clean_db)

    res = client.post(
        f"/api/teintes/{teinte.id}/image", files={"fichier": ("n.png", PNG, "image/png")},
        headers=_headers(clean_db),
    )

    assert res.status_code == 200
    assert "/uploads/" in res.json()["image_url"]


def test_delete_teinte_libre_204(clean_db):
    teinte = _teinte(clean_db)

    assert client.delete(f"/api/teintes/{teinte.id}", headers=_headers(clean_db)).status_code == 204


def test_delete_teinte_proposee_409(clean_db):
    teinte = _teinte(clean_db)
    h = _headers(clean_db)
    client.post("/api/produits", json=_produit_payload(clean_db, teinte_ids=[teinte.id]), headers=h)

    res = client.delete(f"/api/teintes/{teinte.id}", headers=h)

    assert res.status_code == 409
    assert res.json()["detail"] == "Teinte proposée par des produits : désactivez-la"


def test_create_produit_avec_teintes(clean_db):
    b = _teinte(clean_db, "B", ordre=2)
    a = _teinte(clean_db, "A", ordre=1)

    res = client.post(
        "/api/produits", json=_produit_payload(clean_db, teinte_ids=[b.id, a.id]),
        headers=_headers(clean_db),
    )

    assert res.status_code == 201
    assert [t["id"] for t in res.json()["teintes"]] == [a.id, b.id]


def test_update_produit_teinte_ids_vide_retire_tout(clean_db):
    teinte = _teinte(clean_db)
    h = _headers(clean_db)
    produit = client.post("/api/produits", json=_produit_payload(clean_db, teinte_ids=[teinte.id]), headers=h).json()

    sans_changement = client.put(f"/api/produits/{produit['id']}", json={"nom": "Autre"}, headers=h)
    vide = client.put(f"/api/produits/{produit['id']}", json={"teinte_ids": []}, headers=h)

    assert len(sans_changement.json()["teintes"]) == 1
    assert vide.json()["teintes"] == []


def test_create_produit_teinte_inconnue_422_et_rien_n_est_cree(clean_db):
    res = client.post(
        "/api/produits", json=_produit_payload(clean_db, teinte_ids=[999999]),
        headers=_headers(clean_db),
    )

    assert res.status_code == 422
    assert res.json()["detail"] == "Teinte introuvable"
    assert clean_db.query(Produit).count() == 0
