import io

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.admin import Admin
from app.models.categorie import Categorie
from app.models.photo import Photo
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


def _make_produit(db):
    categorie = Categorie(nom="Tables", slug="tables")
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
    db.refresh(produit)
    return produit


@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()
    db.query(Photo).delete()
    db.query(Produit).delete()
    db.query(Categorie).delete()
    db.query(Admin).delete()
    db.commit()
    yield db
    db.query(Photo).delete()
    db.query(Produit).delete()
    db.query(Categorie).delete()
    db.query(Admin).delete()
    db.commit()
    db.close()


def test_add_photo_uploads_file_and_serves_it_back(clean_db):
    db = clean_db
    token = _admin_token(db)
    produit = _make_produit(db)

    res = client.post(
        f"/api/produits/{produit.id}/photos",
        files={"fichier": ("chaise.jpg", io.BytesIO(b"fake-image-bytes"), "image/jpeg")},
        data={"ordre": "1"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 201
    body = res.json()
    assert body["produit_id"] == produit.id
    assert body["principale"] is False

    served = client.get(body["url"].replace("http://localhost:3000", ""))
    assert served.status_code == 200
    assert served.content == b"fake-image-bytes"


def test_add_photo_returns_404_for_unknown_produit(clean_db):
    token = _admin_token(clean_db)

    res = client.post(
        "/api/produits/999/photos",
        files={"fichier": ("chaise.jpg", io.BytesIO(b"x"), "image/jpeg")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 404


def test_set_principale_unsets_previous_principale(clean_db):
    db = clean_db
    token = _admin_token(db)
    produit = _make_produit(db)
    headers = {"Authorization": f"Bearer {token}"}

    first = client.post(
        f"/api/produits/{produit.id}/photos",
        files={"fichier": ("a.jpg", io.BytesIO(b"a"), "image/jpeg")},
        headers=headers,
    ).json()
    second = client.post(
        f"/api/produits/{produit.id}/photos",
        files={"fichier": ("b.jpg", io.BytesIO(b"b"), "image/jpeg")},
        headers=headers,
    ).json()

    client.patch(f"/api/photos/{first['id']}/principale", headers=headers)
    res = client.patch(f"/api/photos/{second['id']}/principale", headers=headers)

    assert res.status_code == 200
    assert res.json()["principale"] is True

    first_after = db.query(Photo).filter(Photo.id == first["id"]).first()
    assert first_after.principale is False


def test_delete_photo(clean_db):
    db = clean_db
    token = _admin_token(db)
    produit = _make_produit(db)
    headers = {"Authorization": f"Bearer {token}"}

    photo = client.post(
        f"/api/produits/{produit.id}/photos",
        files={"fichier": ("a.jpg", io.BytesIO(b"a"), "image/jpeg")},
        headers=headers,
    ).json()

    res = client.delete(f"/api/photos/{photo['id']}", headers=headers)
    assert res.status_code == 204

    remaining = db.query(Photo).filter(Photo.id == photo["id"]).first()
    assert remaining is None
