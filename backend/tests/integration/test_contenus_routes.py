import io

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.admin import Admin
from app.models.contenu import ContenuSite
from app.services import auth_service

client = TestClient(app)
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 20


@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()

    def vider():
        db.query(ContenuSite).delete()
        db.query(Admin).delete()
        db.commit()

    vider()
    yield db
    vider()
    db.close()


@pytest.fixture
def admin(clean_db):
    clean_db.add(Admin(email="admin@test.com", password_hash=auth_service.hash_password("test-password-123")))
    clean_db.commit()
    return {"Authorization": f"Bearer {auth_service.login(clean_db, 'admin@test.com', 'test-password-123')}"}


def _image(admin, cle="boutique.ceramique_image", nom="v.png"):
    return client.post(f"/api/contenus/{cle}/image", files={"fichier": (nom, io.BytesIO(PNG), "image/png")}, headers=admin)


def test_aucun_contenu_modifie_au_depart_le_site_garde_ses_textes_d_origine():
    assert client.get("/api/contenus").json() == {}


def test_modifier_un_texte_puis_le_lire_sans_etre_connecte(admin):
    res = client.put("/api/contenus/accueil.titre", json={"texte": "  Du bois et de la terre  "}, headers=admin)

    assert res.status_code == 200 and res.json() == {"cle": "accueil.titre", "texte": "Du bois et de la terre", "image_url": None}
    assert client.get("/api/contenus").json()["accueil.titre"]["texte"] == "Du bois et de la terre"
    client.put("/api/contenus/accueil.titre", json={"texte": "Autre"}, headers=admin)
    assert client.get("/api/contenus").json()["accueil.titre"]["texte"] == "Autre"


def test_un_texte_vide_retablit_le_texte_d_origine(admin):
    client.put("/api/contenus/accueil.titre", json={"texte": "Modifié"}, headers=admin)

    res = client.put("/api/contenus/accueil.titre", json={"texte": "   "}, headers=admin)

    assert res.status_code == 200
    assert "accueil.titre" not in client.get("/api/contenus").json()


def test_une_cle_inconnue_ou_du_mauvais_type_est_refusee(admin):
    assert client.put("/api/contenus/n.importe.quoi", json={"texte": "x"}, headers=admin).status_code == 404
    assert client.put("/api/contenus/boutique.ceramique_image", json={"texte": "x"}, headers=admin).status_code == 422
    assert _image(admin, "accueil.titre").status_code == 422
    assert _image(admin, "inconnue").status_code == 404
    assert client.put("/api/contenus/accueil.titre", json={"texte": "x" * 5001}, headers=admin).status_code == 422


def test_changer_une_photo_puis_la_retablir(admin):
    res = _image(admin)

    assert res.status_code == 200 and "/uploads/" in res.json()["image_url"]
    assert client.get("/api/contenus").json()["boutique.ceramique_image"]["image_url"] == res.json()["image_url"]

    assert client.delete("/api/contenus/boutique.ceramique_image", headers=admin).status_code == 204
    assert "boutique.ceramique_image" not in client.get("/api/contenus").json()
    assert client.delete("/api/contenus/boutique.ceramique_image", headers=admin).status_code == 204  # nothing to reset: still fine
    assert client.delete("/api/contenus/inconnue", headers=admin).status_code == 404


def test_une_photo_qui_n_est_pas_une_image_est_refusee(admin):
    res = client.post(
        "/api/contenus/boutique.ceramique_image/image",
        files={"fichier": ("v.html", io.BytesIO(b"<b>"), "text/html")}, headers=admin,
    )

    assert res.status_code == 422
    assert client.get("/api/contenus").json() == {}


def test_texte_et_photo_d_une_meme_cle_sont_independants(admin):
    client.put("/api/contenus/accueil.univers_titre", json={"texte": "Titre"}, headers=admin)
    assert client.get("/api/contenus").json()["accueil.univers_titre"]["image_url"] is None
