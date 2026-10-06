import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.admin import Admin
from app.models.categorie import Categorie
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


def _make_categorie(db, nom="Tables", slug="tables"):
    categorie = Categorie(nom=nom, slug=slug)
    db.add(categorie)
    db.commit()
    db.refresh(categorie)
    return categorie


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


def test_create_produit_requires_admin(clean_db):
    categorie = _make_categorie(clean_db)

    res = client.post(
        "/api/produits",
        json={
            "nom": "Table basse",
            "description": "En chêne",
            "categorie_id": categorie.id,
            "prix": "199.99",
            "dimensions": "120x60x40cm",
            "disponibilite": "disponible",
        },
    )

    assert res.status_code == 401


def test_create_and_get_produit(clean_db):
    token = _admin_token(clean_db)
    categorie = _make_categorie(clean_db)

    create_res = client.post(
        "/api/produits",
        json={
            "nom": "Table basse",
            "description": "En chêne",
            "categorie_id": categorie.id,
            "prix": "199.99",
            "dimensions": "120x60x40cm",
            "disponibilite": "disponible",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_res.status_code == 201
    produit_id = create_res.json()["id"]

    get_res = client.get(f"/api/produits/{produit_id}")
    assert get_res.status_code == 200
    assert get_res.json()["nom"] == "Table basse"


def test_get_produit_returns_404_when_not_found(clean_db):
    res = client.get("/api/produits/999")
    assert res.status_code == 404


def test_list_produits_filters_by_categorie(clean_db):
    db = clean_db
    token = _admin_token(db)
    cat_tables = _make_categorie(db, "Tables", "tables")
    cat_chaises = _make_categorie(db, "Chaises", "chaises")

    for nom, cat in [("Table basse", cat_tables), ("Chaise haute", cat_chaises)]:
        client.post(
            "/api/produits",
            json={
                "nom": nom,
                "description": "desc",
                "categorie_id": cat.id,
                "prix": "50.00",
                "dimensions": "10x10x10cm",
                "disponibilite": "disponible",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    res = client.get(f"/api/produits?categorie={cat_tables.id}")
    assert res.status_code == 200
    noms = [p["nom"] for p in res.json()]
    assert noms == ["Table basse"]


def test_update_produit_partial_fields(clean_db):
    db = clean_db
    token = _admin_token(db)
    categorie = _make_categorie(db)

    create_res = client.post(
        "/api/produits",
        json={
            "nom": "Table basse",
            "description": "En chêne",
            "categorie_id": categorie.id,
            "prix": "199.99",
            "dimensions": "120x60x40cm",
            "disponibilite": "disponible",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    produit_id = create_res.json()["id"]

    update_res = client.put(
        f"/api/produits/{produit_id}",
        json={"disponibilite": "rupture"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert update_res.status_code == 200
    assert update_res.json()["disponibilite"] == "rupture"
    assert update_res.json()["nom"] == "Table basse"  # untouched


def test_delete_produit(clean_db):
    db = clean_db
    token = _admin_token(db)
    categorie = _make_categorie(db)

    create_res = client.post(
        "/api/produits",
        json={
            "nom": "Table basse",
            "description": "En chêne",
            "categorie_id": categorie.id,
            "prix": "199.99",
            "dimensions": "120x60x40cm",
            "disponibilite": "disponible",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    produit_id = create_res.json()["id"]

    delete_res = client.delete(
        f"/api/produits/{produit_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_res.status_code == 204

    get_res = client.get(f"/api/produits/{produit_id}")
    assert get_res.status_code == 404
