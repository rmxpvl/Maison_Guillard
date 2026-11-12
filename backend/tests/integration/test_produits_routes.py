import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.admin import Admin
from app.models.categorie import Categorie, Univers
from app.models.photo import Photo
from app.models.produit import Produit
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
    categorie = Categorie(nom=nom, slug=slug, univers=Univers.meubles)
    db.add(categorie)
    db.commit()
    db.refresh(categorie)
    return categorie


def _make_produit_avec_photos(db, categorie, ordres):
    produit = Produit(
        nom="Table basse",
        description="En chêne",
        categorie_id=categorie.id,
        prix=199.99,
        dimensions="120x60x40cm",
        visible=True,
    )
    db.add(produit)
    db.commit()
    db.refresh(produit)
    for ordre in ordres:
        db.add(
            Photo(
                produit_id=produit.id,
                url=f"https://example.com/photo-{ordre}.jpg",
                ordre=ordre,
                principale=False,
            )
        )
    db.commit()
    return produit


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
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    produit_id = create_res.json()["id"]

    update_res = client.put(
        f"/api/produits/{produit_id}",
        json={"visible": False},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert update_res.status_code == 200
    assert update_res.json()["visible"] is False
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


def test_create_produit_returns_422_when_categorie_does_not_exist(clean_db):
    token = _admin_token(clean_db)

    res = client.post(
        "/api/produits",
        json={
            "nom": "Table basse",
            "description": "En chêne",
            "categorie_id": 999999,
            "prix": "199.99",
            "dimensions": "120x60x40cm",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 422


def test_update_produit_returns_422_when_categorie_does_not_exist(clean_db):
    db = clean_db
    token = _admin_token(db)
    categorie = _make_categorie(db)
    headers = {"Authorization": f"Bearer {token}"}
    create_res = client.post(
        "/api/produits",
        json={
            "nom": "Table basse",
            "description": "En chêne",
            "categorie_id": categorie.id,
            "prix": "199.99",
            "dimensions": "120x60x40cm",
        },
        headers=headers,
    )

    res = client.put(
        f"/api/produits/{create_res.json()['id']}",
        json={"categorie_id": 999999},
        headers=headers,
    )

    assert res.status_code == 422


def _make_produit_masque(db, categorie, nom="Caché"):
    produit = Produit(
        nom=nom, description="d", categorie_id=categorie.id, prix=10,
        dimensions="1x1", visible=False,
    )
    db.add(produit)
    db.commit()
    db.refresh(produit)
    return produit


def test_list_produits_public_cache_les_produits_masques(clean_db):
    categorie = _make_categorie(clean_db)
    _make_produit_avec_photos(clean_db, categorie, [])
    _make_produit_masque(clean_db, categorie)
    headers = {"Authorization": f"Bearer {_admin_token(clean_db)}"}

    assert len(client.get("/api/produits").json()) == 1
    assert len(client.get("/api/produits/admin", headers=headers).json()) == 2


def test_get_produit_masque_404_en_public_200_en_admin(clean_db):
    categorie = _make_categorie(clean_db)
    produit = _make_produit_masque(clean_db, categorie)
    headers = {"Authorization": f"Bearer {_admin_token(clean_db)}"}

    public = client.get(f"/api/produits/{produit.id}")
    admin = client.get(f"/api/produits/admin/{produit.id}", headers=headers)

    assert public.status_code == 404
    assert public.json()["detail"] == "Produit introuvable"
    assert admin.status_code == 200
    assert admin.json()["visible"] is False


def test_get_produit_admin_404_si_absent(clean_db):
    headers = {"Authorization": f"Bearer {_admin_token(clean_db)}"}

    assert client.get("/api/produits/admin/999999", headers=headers).status_code == 404


def test_get_produit_includes_photos_sorted_by_ordre(clean_db):
    categorie = _make_categorie(clean_db)
    produit = _make_produit_avec_photos(clean_db, categorie, ordres=[2, 0, 1])

    res = client.get(f"/api/produits/{produit.id}")

    assert res.status_code == 200
    assert [p["ordre"] for p in res.json()["photos"]] == [0, 1, 2]


def test_list_produits_includes_photos_sorted_by_ordre(clean_db):
    categorie = _make_categorie(clean_db)
    _make_produit_avec_photos(clean_db, categorie, ordres=[2, 0, 1])

    res = client.get("/api/produits")

    assert res.status_code == 200
    assert [p["ordre"] for p in res.json()[0]["photos"]] == [0, 1, 2]


def test_produit_without_photo_returns_empty_photos_list(clean_db):
    categorie = _make_categorie(clean_db)
    produit = _make_produit_avec_photos(clean_db, categorie, ordres=[])

    res = client.get(f"/api/produits/{produit.id}")

    assert res.status_code == 200
    assert res.json()["photos"] == []


def test_delete_produit_with_photos_removes_its_photos(clean_db):
    token = _admin_token(clean_db)
    categorie = _make_categorie(clean_db)
    produit = _make_produit_avec_photos(clean_db, categorie, ordres=[0, 1])
    produit_id = produit.id

    res = client.delete(
        f"/api/produits/{produit_id}", headers={"Authorization": f"Bearer {token}"}
    )

    assert res.status_code == 204
    assert clean_db.query(Photo).filter(Photo.produit_id == produit_id).count() == 0

def test_list_produits_filtre_par_univers(clean_db):
    meuble = _make_categorie(clean_db, "Tables", "tables")
    ceramique = Categorie(nom="Vases", slug="vases", univers=Univers.ceramique)
    clean_db.add(ceramique)
    clean_db.commit()
    _make_produit_avec_photos(clean_db, meuble, [])
    vase = _make_produit_avec_photos(clean_db, ceramique, [])

    res = client.get("/api/produits?univers=ceramique")

    assert res.status_code == 200
    assert [p["id"] for p in res.json()] == [vase.id]


def test_list_produits_422_pour_un_univers_inconnu(clean_db):
    assert client.get("/api/produits?univers=jardin").status_code == 422
