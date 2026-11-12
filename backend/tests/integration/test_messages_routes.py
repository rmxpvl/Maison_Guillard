import re
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.admin import Admin
from app.models.categorie import Categorie, Univers
from app.models.client import Client, JetonClient
from app.models.demande import Demande
from app.models.message_demande import MessageDemande
from app.models.produit import Produit
from app.services import auth_service

client = TestClient(app)
MDP = "un-mot-de-passe-solide"


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("SITE_URL", "https://maison.test")
    monkeypatch.setenv("EMAIL_ARTISAN", "artisan@test.com")
    monkeypatch.setenv("EMAIL_EXPEDITEUR", "site@test.com")


@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()

    def vider():
        for modele in (MessageDemande, Demande, JetonClient, Client, Produit, Categorie, Admin):
            db.query(modele).delete()
        db.commit()

    vider()
    yield db
    vider()
    db.close()


@pytest.fixture(autouse=True)
def courriel():
    with patch("app.services.email_service.envoyer") as envoi:
        yield envoi


@pytest.fixture
def admin(clean_db):
    clean_db.add(Admin(email="admin@test.com", password_hash=auth_service.hash_password("test-password-123")))
    clean_db.commit()
    return {"Authorization": f"Bearer {auth_service.login(clean_db, 'admin@test.com', 'test-password-123')}"}


def _demande(db, email="jeanne@test.com"):
    categorie = db.query(Categorie).first() or Categorie(nom="Tables", slug="tables", univers=Univers.meubles)
    db.add(categorie)
    db.commit()
    produit = Produit(nom="Table", description="d", categorie_id=categorie.id, prix=100, dimensions="1x1")
    db.add(produit)
    db.commit()
    return client.post("/api/demandes", json={
        "nom_client": "Jeanne", "email": email, "adresse": "1 rue du Bois",
        "lignes": [{"produit_id": produit.id, "quantite": 1}],
    }).json()


def _dernier_courriel(courriel):
    (messages,), _ = courriel.call_args
    return messages[0]


# ---------- le client, par son lien secret ----------

def test_le_client_ecrit_et_relit_son_fil(clean_db):
    demande = _demande(clean_db)
    url = f"/api/demandes/suivi/{demande['jeton']}/messages"

    cree = client.post(url, json={"texte": "Bonjour, une question sur la finition"})
    fil = client.get(url)

    assert cree.status_code == 201
    assert cree.json()["auteur"] == "client" and cree.json()["texte"] == "Bonjour, une question sur la finition"
    assert [m["texte"] for m in fil.json()] == ["Bonjour, une question sur la finition"]
    assert "id" in fil.json()[0] and "created_at" in fil.json()[0]


def test_fil_inconnu_ou_message_invalide(clean_db):
    demande = _demande(clean_db)
    url = f"/api/demandes/suivi/{demande['jeton']}/messages"

    assert client.get("/api/demandes/suivi/inconnu/messages").status_code == 404
    assert client.post("/api/demandes/suivi/inconnu/messages", json={"texte": "x"}).status_code == 404
    assert client.post(url, json={"texte": "   "}).status_code == 422
    assert client.post(url, json={"texte": "x" * 2001}).status_code == 422
    assert clean_db.query(MessageDemande).count() == 0


def test_chaque_fil_est_prive(clean_db):
    a = _demande(clean_db, "a@test.com")
    b = _demande(clean_db, "b@test.com")
    client.post(f"/api/demandes/suivi/{a['jeton']}/messages", json={"texte": "secret de A"})

    assert client.get(f"/api/demandes/suivi/{b['jeton']}/messages").json() == []


def test_un_message_du_client_previent_l_artisane(clean_db, courriel):
    demande = _demande(clean_db)
    courriel.reset_mock()

    client.post(f"/api/demandes/suivi/{demande['jeton']}/messages", json={"texte": "Bonjour"})

    mail = _dernier_courriel(courriel)
    assert mail["To"] == "artisan@test.com" and f"n°{demande['id']}" in mail["Subject"]
    assert "Bonjour" in mail.get_content()


# ---------- l'artisane ----------

def test_l_artisane_repond_et_le_client_est_prevenu_par_e_mail(clean_db, admin, courriel):
    demande = _demande(clean_db)
    courriel.reset_mock()

    res = client.post(f"/api/demandes/{demande['id']}/messages", json={"texte": "Avec plaisir, voici ma réponse"}, headers=admin)

    assert res.status_code == 201 and res.json()["auteur"] == "artisane"
    mail = _dernier_courriel(courriel)
    assert mail["To"] == "jeanne@test.com"
    assert f"https://maison.test/devis/{demande['jeton']}" in mail.get_content()
    fil = client.get(f"/api/demandes/suivi/{demande['jeton']}/messages").json()
    assert [m["auteur"] for m in fil] == ["artisane"]


def test_fil_cote_admin_et_404(clean_db, admin):
    demande = _demande(clean_db)
    client.post(f"/api/demandes/suivi/{demande['jeton']}/messages", json={"texte": "Bonjour"})

    fil = client.get(f"/api/demandes/{demande['id']}/messages", headers=admin)

    assert [m["auteur"] for m in fil.json()] == ["client"]
    assert client.get("/api/demandes/999999/messages", headers=admin).status_code == 404
    assert client.post("/api/demandes/999999/messages", json={"texte": "x"}, headers=admin).status_code == 404


# ---------- non lus ----------

def test_non_lus_cote_artisane(clean_db, admin):
    demande = _demande(clean_db)
    for texte in ("un", "deux"):
        client.post(f"/api/demandes/suivi/{demande['jeton']}/messages", json={"texte": texte})

    liste = client.get("/api/demandes", headers=admin).json()
    detail = client.get(f"/api/demandes/{demande['id']}", headers=admin).json()
    assert liste[0]["messages_non_lus"] == 2 and detail["messages_non_lus"] == 2

    client.get(f"/api/demandes/{demande['id']}/messages", headers=admin)  # she reads the thread

    assert client.get("/api/demandes", headers=admin).json()[0]["messages_non_lus"] == 0


def test_non_lus_cote_client_dans_mon_compte(clean_db, admin, courriel):
    client.post("/api/clients/inscription", json={"email": "jeanne@test.com"})
    jeton_mail = re.search(r"token=([\w-]+)", _dernier_courriel(courriel).get_content()).group(1)
    demande = _demande(clean_db)
    compte = client.post("/api/clients/activer", json={"token": jeton_mail, "mot_de_passe": MDP}).json()["token"]
    en_tete = {"Authorization": f"Bearer {compte}"}
    client.post(f"/api/demandes/{demande['id']}/messages", json={"texte": "Bonjour Jeanne"}, headers=admin)

    avant = client.get("/api/clients/moi", headers=en_tete).json()["demandes"][0]
    assert avant["messages_non_lus"] == 1

    client.get(f"/api/demandes/suivi/{demande['jeton']}/messages")  # the customer opens her thread

    assert client.get("/api/clients/moi", headers=en_tete).json()["demandes"][0]["messages_non_lus"] == 0


def test_ses_propres_messages_ne_comptent_pas_comme_non_lus(clean_db, admin):
    demande = _demande(clean_db)
    client.post(f"/api/demandes/{demande['id']}/messages", json={"texte": "Note de l'atelier"}, headers=admin)

    assert client.get("/api/demandes", headers=admin).json()[0]["messages_non_lus"] == 0
