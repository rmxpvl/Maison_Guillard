import io
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.actualite import Actualite, PhotoActualite
from app.models.admin import Admin
from app.services import auth_service

client = TestClient(app)
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 20


@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()

    def vider():
        db.query(Actualite).delete()
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


def _creer(admin, titre="Nouvelle collection", **extra):
    corps = {"titre": titre, "contenu": "Premier paragraphe.\n\nSecond paragraphe.", **extra}
    res = client.post("/api/actualites", json=corps, headers=admin)
    assert res.status_code == 201, res.text
    return res.json()


def _photo(admin, actualite_id, nom="a.png"):
    return client.post(
        f"/api/actualites/{actualite_id}/photos",
        files={"fichier": (nom, io.BytesIO(PNG), "image/png")},
        headers=admin,
    )


# ---------- ecrire ----------

def test_creer_une_actualite_donne_une_adresse_et_reste_brouillon_par_defaut(admin):
    a = _creer(admin, "Nouvelle collection d'automne")

    assert a["slug"] == "nouvelle-collection-d-automne"
    assert a["publiee"] is False and a["photos"] == []
    assert a["date_publication"]


def test_deux_actualites_au_meme_titre_ont_des_adresses_differentes(admin):
    assert [_creer(admin, "Mon titre")["slug"] for _ in range(3)] == ["mon-titre", "mon-titre-2", "mon-titre-3"]


def test_modifier_le_titre_ne_change_pas_l_adresse(admin):
    a = _creer(admin, "Titre d'origine")

    res = client.put(f"/api/actualites/{a['id']}", json={"titre": "Un tout autre titre"}, headers=admin)

    assert res.status_code == 200
    assert res.json()["titre"] == "Un tout autre titre" and res.json()["slug"] == "titre-d-origine"


def test_modifier_ne_touche_que_les_champs_envoyes(admin):
    a = _creer(admin, "Titre", publiee=True)

    res = client.put(f"/api/actualites/{a['id']}", json={"contenu": "Nouveau texte"}, headers=admin)

    assert res.json()["contenu"] == "Nouveau texte" and res.json()["titre"] == "Titre" and res.json()["publiee"] is True


@pytest.mark.parametrize("corps", [
    {"titre": "", "contenu": "x"}, {"titre": "   ", "contenu": "x"}, {"titre": "x" * 151, "contenu": "x"},
    {"titre": "Titre", "contenu": ""}, {"titre": "Titre", "contenu": "x" * 20001},
])
def test_creer_refuse_des_champs_invalides(admin, corps):
    assert client.post("/api/actualites", json=corps, headers=admin).status_code == 422


def test_modifier_ou_supprimer_une_actualite_inconnue_404(admin):
    assert client.put("/api/actualites/999999", json={"titre": "x"}, headers=admin).status_code == 404
    assert client.delete("/api/actualites/999999", headers=admin).status_code == 404


def test_supprimer_une_actualite_supprime_ses_photos(admin, clean_db):
    a = _creer(admin)
    _photo(admin, a["id"])

    assert client.delete(f"/api/actualites/{a['id']}", headers=admin).status_code == 204

    assert clean_db.query(Actualite).count() == 0 and clean_db.query(PhotoActualite).count() == 0


# ---------- lire ----------

def test_le_public_ne_voit_que_les_actualites_publiees(admin):
    publiee = _creer(admin, "Publiée", publiee=True)
    _creer(admin, "Brouillon")

    liste = client.get("/api/actualites").json()

    assert [a["id"] for a in liste] == [publiee["id"]]
    assert client.get("/api/actualites/brouillon").status_code == 404
    assert client.get(f"/api/actualites/{publiee['slug']}").json()["titre"] == "Publiée"
    assert client.get("/api/actualites/inconnue").status_code == 404


def test_les_plus_recentes_d_abord(admin):
    maintenant = datetime.now(timezone.utc)
    ancienne = _creer(admin, "Ancienne", publiee=True, date_publication=(maintenant - timedelta(days=30)).isoformat())
    recente = _creer(admin, "Récente", publiee=True, date_publication=maintenant.isoformat())

    assert [a["id"] for a in client.get("/api/actualites").json()] == [recente["id"], ancienne["id"]]


def test_l_administration_voit_aussi_les_brouillons(admin):
    brouillon = _creer(admin, "Brouillon")

    tout = client.get("/api/actualites/admin", headers=admin).json()
    un = client.get(f"/api/actualites/admin/{brouillon['id']}", headers=admin)

    assert [a["id"] for a in tout] == [brouillon["id"]]
    assert un.status_code == 200 and un.json()["publiee"] is False
    assert client.get("/api/actualites/admin/999999", headers=admin).status_code == 404


def test_une_actualite_intitulee_admin_ne_cache_pas_la_route_d_administration(admin):
    a = _creer(admin, "Admin", publiee=True)

    assert a["slug"] != "admin"
    assert client.get("/api/actualites/admin", headers=admin).status_code == 200


# ---------- photos ----------

def test_ajouter_des_photos_la_premiere_est_la_couverture(admin):
    a = _creer(admin)

    premiere = _photo(admin, a["id"], "1.png")
    seconde = _photo(admin, a["id"], "2.png")

    assert premiere.status_code == 201 and "/uploads/" in premiere.json()["url"]
    lu = client.get(f"/api/actualites/admin/{a['id']}", headers=admin).json()
    assert [p["id"] for p in lu["photos"]] == [premiere.json()["id"], seconde.json()["id"]]


def test_photo_refuse_un_fichier_qui_n_est_pas_une_image_et_une_actualite_inconnue(admin):
    a = _creer(admin)

    mauvais = client.post(f"/api/actualites/{a['id']}/photos", files={"fichier": ("a.html", io.BytesIO(b"<b>"), "text/html")}, headers=admin)

    assert mauvais.status_code == 422 and "Format non accepté" in mauvais.json()["detail"]
    assert _photo(admin, 999999).status_code == 404


def test_choisir_la_couverture_met_la_photo_en_premier(admin):
    a = _creer(admin, publiee=True)
    p1 = _photo(admin, a["id"], "1.png").json()
    p2 = _photo(admin, a["id"], "2.png").json()
    p3 = _photo(admin, a["id"], "3.png").json()

    res = client.patch(f"/api/actualites/photos/{p3['id']}/couverture", headers=admin)

    assert res.status_code == 200
    ordre = [p["id"] for p in client.get(f"/api/actualites/{a['slug']}").json()["photos"]]
    assert ordre == [p3["id"], p1["id"], p2["id"]]


def test_legende_et_suppression_d_une_photo(admin):
    a = _creer(admin)
    p = _photo(admin, a["id"]).json()

    legende = client.patch(f"/api/actualites/photos/{p['id']}", json={"legende": " Le tour de bras "}, headers=admin)
    supprime = client.delete(f"/api/actualites/photos/{p['id']}", headers=admin)

    assert legende.json()["legende"] == "Le tour de bras"
    assert supprime.status_code == 204
    assert client.get(f"/api/actualites/admin/{a['id']}", headers=admin).json()["photos"] == []
    assert client.delete(f"/api/actualites/photos/{p['id']}", headers=admin).status_code == 404
    assert client.patch("/api/actualites/photos/999999/couverture", headers=admin).status_code == 404
