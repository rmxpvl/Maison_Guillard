import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.admin import Admin
from app.models.categorie import Categorie, Univers
from app.models.produit import Produit, Disponibilite
from app.services import auth_service

client = TestClient(app)


def _admin_token(db):
    db.query(Admin).delete()
    db.commit()
    admin = Admin(
        email="admin@test.com",
        password_hash=auth_service.hash_password("test-password-123"),
    )
    db.add(admin)
    db.commit()
    return auth_service.login(db, "admin@test.com", "test-password-123")


@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()
    db.query(Produit).delete()
    db.query(Categorie).delete()
    db.query(Admin).delete()
    db.commit()
    yield db
    db.query(Produit).delete()
    db.query(Categorie).delete()
    db.query(Admin).delete()
    db.commit()
    db.close()


def test_list_categories_returns_empty_list_initially(clean_db):
    res = client.get("/api/categories")
    assert res.status_code == 200
    assert res.json() == []


def test_create_categorie_requires_admin(clean_db):
    res = client.post("/api/categories", json={"nom": "Tables", "slug": "tables", "univers": "meubles"})
    assert res.status_code == 401


def test_create_categorie_succeeds_with_admin_token(clean_db):
    token = _admin_token(clean_db)

    res = client.post(
        "/api/categories",
        json={"nom": "Tables", "slug": "tables", "univers": "meubles"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 201
    assert res.json()["slug"] == "tables"


def test_delete_categorie_returns_404_when_not_found(clean_db):
    token = _admin_token(clean_db)

    res = client.delete(
        "/api/categories/999", headers={"Authorization": f"Bearer {token}"}
    )

    assert res.status_code == 404


def test_delete_categorie_returns_409_when_used_by_a_produit(clean_db):
    db = clean_db
    token = _admin_token(db)

    categorie = Categorie(nom="Tables", slug="tables", univers=Univers.meubles)
    db.add(categorie)
    db.commit()
    db.refresh(categorie)

    produit = Produit(
        nom="Table basse",
        description="En chêne",
        categorie_id=categorie.id,
        prix=199.99,
        dimensions="120x60x40cm",
        disponibilite=Disponibilite.disponible,
    )
    db.add(produit)
    db.commit()

    res = client.delete(
        f"/api/categories/{categorie.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 409


def test_delete_categorie_succeeds_when_unused(clean_db):
    db = clean_db
    token = _admin_token(db)

    categorie = Categorie(nom="Chaises", slug="chaises", univers=Univers.meubles)
    db.add(categorie)
    db.commit()
    db.refresh(categorie)

    res = client.delete(
        f"/api/categories/{categorie.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 204


def test_create_categorie_returns_409_when_slug_already_exists(clean_db):
    token = _admin_token(clean_db)
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/api/categories", json={"nom": "Tables", "slug": "tables", "univers": "meubles"}, headers=headers)

    res = client.post(
        "/api/categories",
        json={"nom": "Tables bis", "slug": "tables", "univers": "meubles"},
        headers=headers,
    )

    assert res.status_code == 409

def _auth(db):
    return {"Authorization": f"Bearer {_admin_token(db)}"}


def test_create_categorie_enregistre_son_univers(clean_db):
    res = client.post(
        "/api/categories",
        json={"nom": "Bols", "slug": "bols", "univers": "ceramique"},
        headers=_auth(clean_db),
    )

    assert res.status_code == 201
    assert res.json()["univers"] == "ceramique"


def test_create_categorie_refuse_un_univers_inconnu(clean_db):
    res = client.post(
        "/api/categories",
        json={"nom": "Bols", "slug": "bols", "univers": "jardin"},
        headers=_auth(clean_db),
    )

    assert res.status_code == 422


def test_update_categorie_change_d_univers_et_garde_ses_produits(clean_db):
    categorie = Categorie(nom="Cartes", slug="cartes", univers=Univers.meubles)
    clean_db.add(categorie)
    clean_db.commit()
    produit = Produit(
        nom="Carte", description="d", categorie_id=categorie.id, prix=5,
        dimensions="A6", disponibilite=Disponibilite.disponible,
    )
    clean_db.add(produit)
    clean_db.commit()

    res = client.put(
        f"/api/categories/{categorie.id}",
        json={"univers": "papeterie", "slug": "carnets"},
        headers=_auth(clean_db),
    )

    assert res.status_code == 200
    assert res.json()["univers"] == "papeterie"
    assert res.json()["slug"] == "carnets"
    clean_db.refresh(produit)
    assert produit.categorie_id == categorie.id


def test_update_categorie_404(clean_db):
    res = client.put("/api/categories/999999", json={"nom": "X"}, headers=_auth(clean_db))

    assert res.status_code == 404
    assert res.json()["detail"] == "Catégorie introuvable"


def test_update_categorie_409_slug_pris(clean_db):
    clean_db.add(Categorie(nom="A", slug="a", univers=Univers.meubles))
    autre = Categorie(nom="B", slug="b", univers=Univers.meubles)
    clean_db.add(autre)
    clean_db.commit()

    res = client.put(f"/api/categories/{autre.id}", json={"slug": "a"}, headers=_auth(clean_db))

    assert res.status_code == 409
    assert res.json()["detail"] == "Slug déjà utilisé"
