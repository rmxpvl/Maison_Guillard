import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.admin import Admin
from app.models.client import Client, JetonClient
from app.services import auth_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()

    def vider():
        db.query(JetonClient).delete()
        db.query(Client).delete()
        db.query(Admin).delete()
        db.commit()

    vider()
    yield db
    vider()
    db.close()


@pytest.fixture(autouse=True)
def pas_d_envoi_reel(monkeypatch):
    monkeypatch.setenv("EMAIL_ARTISAN", "artisan@test.com")
    monkeypatch.setenv("EMAIL_EXPEDITEUR", "site@test.com")
    from unittest.mock import patch

    with patch("app.services.email_service.envoyer"):
        yield


def _connexion_admin(email="admin@test.com"):
    return client.post("/api/auth/login", json={"email": email, "motDePasse": "faux-mot-de-passe"})


def test_la_connexion_admin_est_limitee_et_repond_429_en_francais():
    reponses = [_connexion_admin() for _ in range(11)]

    assert [r.status_code for r in reponses[:10]] == [401] * 10
    assert reponses[10].status_code == 429
    assert "réessayez" in reponses[10].json()["detail"].lower()
    assert int(reponses[10].headers["Retry-After"]) > 0


def test_une_bonne_connexion_admin_compte_aussi_dans_la_limite(clean_db):
    clean_db.add(Admin(email="admin@test.com", password_hash=auth_service.hash_password("test-password-123")))
    clean_db.commit()
    corps = {"email": "admin@test.com", "motDePasse": "test-password-123"}

    statuts = [client.post("/api/auth/login", json=corps).status_code for _ in range(11)]

    assert statuts[:10] == [200] * 10 and statuts[10] == 429


def test_l_inscription_client_est_limitee():
    statuts = [client.post("/api/clients/inscription", json={"email": f"a{i}@test.com"}).status_code for i in range(6)]

    assert statuts[:5] == [200] * 5 and statuts[5] == 429


def test_la_connexion_client_est_limitee_par_adresse_ip():
    corps = {"email": "jeanne@test.com", "mot_de_passe": "faux-mot-de-passe"}
    statuts = [client.post("/api/clients/connexion", json=corps).status_code for _ in range(11)]

    assert statuts[:10] == [401] * 10 and statuts[10] == 429


def test_mot_de_passe_oublie_est_limite_par_adresse_e_mail_meme_depuis_d_autres_ip(monkeypatch):
    # Someone must not be able to flood one mailbox from many addresses.
    monkeypatch.setenv("TRUST_PROXY", "1")
    statuts = [
        client.post("/api/clients/mot-de-passe-oublie", json={"email": "victime@test.com"},
                    headers={"X-Forwarded-For": f"203.0.113.{i}"}).status_code
        for i in range(4)
    ]

    assert statuts == [200, 200, 200, 429]


def test_la_connexion_est_aussi_limitee_par_compte_depuis_plusieurs_ip(monkeypatch):
    # Guessing one account's password from many addresses is stopped by the per-account counter.
    monkeypatch.setenv("TRUST_PROXY", "1")
    corps = {"email": "jeanne@test.com", "mot_de_passe": "faux-mot-de-passe"}
    statuts = [
        client.post("/api/clients/connexion", json=corps, headers={"X-Forwarded-For": f"203.0.113.{i}"}).status_code
        for i in range(12)
    ]

    assert statuts[:10] == [401] * 10 and statuts[10:] == [429, 429]


def test_deux_visiteurs_differents_ne_se_genent_pas(monkeypatch):
    monkeypatch.setenv("TRUST_PROXY", "1")
    for _ in range(10):
        client.post("/api/auth/login", json={"email": "a@test.com", "motDePasse": "x"}, headers={"X-Forwarded-For": "203.0.113.1"})

    bloque = client.post("/api/auth/login", json={"email": "b@test.com", "motDePasse": "x"}, headers={"X-Forwarded-For": "203.0.113.1"})
    autre = client.post("/api/auth/login", json={"email": "c@test.com", "motDePasse": "x"}, headers={"X-Forwarded-For": "203.0.113.2"})

    assert bloque.status_code == 429 and autre.status_code == 401


def test_sans_proxy_de_confiance_un_faux_x_forwarded_for_ne_contourne_pas_la_limite(monkeypatch):
    monkeypatch.delenv("TRUST_PROXY", raising=False)
    statuts = [
        client.post("/api/auth/login", json={"email": f"x{i}@test.com", "motDePasse": "x"},
                    headers={"X-Forwarded-For": f"203.0.113.{i}"}).status_code
        for i in range(11)
    ]

    assert statuts[10] == 429


@pytest.mark.parametrize("methode, url, corps", [
    ("post", "/api/demandes", {"nom_client": "Jeanne", "email": "j@test.com", "adresse": "1 rue", "lignes": []}),
    ("post", "/api/demandes/projet-libre", {"nom_client": "J", "email": "j@test.com", "description_projet": "x"}),
    ("post", "/api/demandes/suivi/inconnu/messages", {"texte": "bonjour"}),
    ("post", "/api/demandes/suivi/inconnu/payer", {"cgv_acceptees": True}),
    ("post", "/api/demandes/suivi/inconnu/annuler", None),
    ("post", "/api/demandes/suivi/inconnu/refuser", None),
    ("post", "/api/clients/activer", {"token": "x", "mot_de_passe": "mot-de-passe-solide"}),
    ("post", "/api/clients/reinitialiser", {"token": "x", "mot_de_passe": "mot-de-passe-solide"}),
])
def test_les_routes_publiques_d_ecriture_sont_toutes_limitees(methode, url, corps):
    statuts = [client.request(methode, url, json=corps).status_code for _ in range(40)]

    assert 429 in statuts


def test_les_lectures_publiques_ne_sont_pas_limitees():
    statuts = {client.get("/api/produits").status_code for _ in range(60)}

    assert statuts == {200}
