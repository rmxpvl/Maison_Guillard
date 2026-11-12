import re
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.admin import Admin
from app.models.categorie import Categorie, Univers
from app.models.client import Client, JetonClient
from app.models.demande import Demande
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
        for modele in (Demande, JetonClient, Client, Produit, Categorie, Admin):
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


def _jeton_dans(courriel, indice=-1) -> str:
    """The token carried by the link of the last e-mail sent."""
    (messages,), _ = courriel.call_args_list[indice]
    corps = messages[0].get_content()
    return re.search(r"token=([\w-]+)", corps).group(1)


def _compte_actif(db, courriel, email="jeanne@test.com"):
    client.post("/api/clients/inscription", json={"email": email})
    res = client.post("/api/clients/activer", json={"token": _jeton_dans(courriel), "mot_de_passe": MDP})
    assert res.status_code == 200
    return res.json()["token"]


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


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


# ---------- inscription et activation ----------

def test_inscription_envoie_un_lien_d_activation_sans_creer_de_mot_de_passe(clean_db, courriel):
    res = client.post("/api/clients/inscription", json={"email": " Jeanne@Test.com "})

    assert res.status_code == 200
    compte = clean_db.query(Client).one()
    assert compte.email == "jeanne@test.com" and compte.password_hash is None and compte.email_verifie_at is None
    (messages,), _ = courriel.call_args
    assert messages[0]["To"] == "jeanne@test.com"
    assert "https://maison.test/compte/activation?token=" in messages[0].get_content()


def test_inscription_est_muette_sur_l_existence_d_un_compte(clean_db, courriel):
    _compte_actif(clean_db, courriel)
    courriel.reset_mock()

    res = client.post("/api/clients/inscription", json={"email": "jeanne@test.com"})

    assert res.status_code == 200 and clean_db.query(Client).count() == 1
    (messages,), _ = courriel.call_args
    assert "token=" not in messages[0].get_content()  # a reminder, not a new link
    assert "mot de passe oublié" in messages[0].get_content().lower()


def test_une_nouvelle_inscription_invalide_le_lien_precedent(clean_db, courriel):
    client.post("/api/clients/inscription", json={"email": "jeanne@test.com"})
    ancien = _jeton_dans(courriel)
    client.post("/api/clients/inscription", json={"email": "jeanne@test.com"})

    assert clean_db.query(Client).count() == 1
    assert client.post("/api/clients/activer", json={"token": ancien, "mot_de_passe": MDP}).status_code == 400
    assert client.post("/api/clients/activer", json={"token": _jeton_dans(courriel), "mot_de_passe": MDP}).status_code == 200


def test_inscription_refuse_une_adresse_invalide(clean_db):
    assert client.post("/api/clients/inscription", json={"email": "nope"}).status_code == 422


def test_activation_choisit_le_mot_de_passe_verifie_l_adresse_et_connecte(clean_db, courriel):
    client.post("/api/clients/inscription", json={"email": "jeanne@test.com"})

    res = client.post("/api/clients/activer", json={"token": _jeton_dans(courriel), "mot_de_passe": MDP})

    assert res.status_code == 200
    compte = clean_db.query(Client).one()
    assert compte.email_verifie_at is not None and compte.password_hash and compte.password_hash != MDP
    assert client.get("/api/clients/moi", headers=_auth(res.json()["token"])).status_code == 200


def test_un_lien_d_activation_ne_sert_qu_une_fois_et_expire(clean_db, courriel):
    client.post("/api/clients/inscription", json={"email": "jeanne@test.com"})
    jeton = _jeton_dans(courriel)
    assert client.post("/api/clients/activer", json={"token": jeton, "mot_de_passe": MDP}).status_code == 200
    assert client.post("/api/clients/activer", json={"token": jeton, "mot_de_passe": "autre-mot-de-passe"}).status_code == 400

    client.post("/api/clients/inscription", json={"email": "paul@test.com"})
    expire = _jeton_dans(courriel)
    for jeton_bdd in clean_db.query(JetonClient).filter(JetonClient.utilise_at.is_(None)):
        jeton_bdd.expire_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    clean_db.commit()
    assert client.post("/api/clients/activer", json={"token": expire, "mot_de_passe": MDP}).status_code == 400
    assert client.post("/api/clients/activer", json={"token": "inconnu", "mot_de_passe": MDP}).status_code == 400


def test_un_mot_de_passe_faible_ne_consomme_pas_le_lien(clean_db, courriel):
    client.post("/api/clients/inscription", json={"email": "jeanne@test.com"})
    jeton = _jeton_dans(courriel)

    assert client.post("/api/clients/activer", json={"token": jeton, "mot_de_passe": "court"}).status_code == 422
    assert client.post("/api/clients/activer", json={"token": jeton, "mot_de_passe": MDP}).status_code == 200


def test_les_jetons_ne_sont_pas_stockes_en_clair(clean_db, courriel):
    client.post("/api/clients/inscription", json={"email": "jeanne@test.com"})

    assert _jeton_dans(courriel) not in [j.token_hash for j in clean_db.query(JetonClient)]


def test_l_activation_rattache_les_demandes_deja_envoyees_avec_cette_adresse(clean_db, courriel):
    a_elle = _demande(clean_db, "Jeanne@Test.com")
    a_un_autre = _demande(clean_db, "paul@test.com")

    _compte_actif(clean_db, courriel)

    compte = clean_db.query(Client).one()
    assert clean_db.query(Demande).get(a_elle["id"]).client_id == compte.id
    assert clean_db.query(Demande).get(a_un_autre["id"]).client_id is None


def test_une_nouvelle_demande_est_rattachee_au_compte_verifie(clean_db, courriel):
    _compte_actif(clean_db, courriel)

    nouvelle = _demande(clean_db)

    assert clean_db.query(Demande).get(nouvelle["id"]).client_id == clean_db.query(Client).one().id


# ---------- connexion ----------

def test_connexion(clean_db, courriel):
    _compte_actif(clean_db, courriel)

    ok = client.post("/api/clients/connexion", json={"email": "JEANNE@test.com", "mot_de_passe": MDP})

    assert ok.status_code == 200 and ok.json()["token"]


def test_connexion_refusee_sans_distinguer_les_cas(clean_db, courriel):
    _compte_actif(clean_db, courriel)
    client.post("/api/clients/inscription", json={"email": "attente@test.com"})  # never activated

    cas = [("jeanne@test.com", "mauvais-mot-de-passe"), ("inconnu@test.com", MDP), ("attente@test.com", MDP)]
    reponses = [client.post("/api/clients/connexion", json={"email": e, "mot_de_passe": m}) for e, m in cas]

    assert [r.status_code for r in reponses] == [401, 401, 401]
    assert len({r.json()["detail"] for r in reponses}) == 1


# ---------- mot de passe oublié ----------

def test_mot_de_passe_oublie_puis_reinitialisation(clean_db, courriel):
    _compte_actif(clean_db, courriel)
    courriel.reset_mock()

    assert client.post("/api/clients/mot-de-passe-oublie", json={"email": "jeanne@test.com"}).status_code == 200
    jeton = _jeton_dans(courriel)
    (messages,), _ = courriel.call_args
    assert "/compte/reinitialisation?token=" in messages[0].get_content()

    nouveau = "nouveau-mot-de-passe-1"
    assert client.post("/api/clients/reinitialiser", json={"token": jeton, "mot_de_passe": nouveau}).status_code == 200
    assert client.post("/api/clients/connexion", json={"email": "jeanne@test.com", "mot_de_passe": MDP}).status_code == 401
    assert client.post("/api/clients/connexion", json={"email": "jeanne@test.com", "mot_de_passe": nouveau}).status_code == 200
    assert client.post("/api/clients/reinitialiser", json={"token": jeton, "mot_de_passe": "encore-un-autre-1"}).status_code == 400


def test_mot_de_passe_oublie_ne_revele_rien(clean_db, courriel):
    courriel.reset_mock()
    client.post("/api/clients/inscription", json={"email": "attente@test.com"})  # unverified account
    courriel.reset_mock()

    inconnu = client.post("/api/clients/mot-de-passe-oublie", json={"email": "inconnu@test.com"})
    non_active = client.post("/api/clients/mot-de-passe-oublie", json={"email": "attente@test.com"})

    assert inconnu.status_code == non_active.status_code == 200 and inconnu.json() == non_active.json()
    courriel.assert_not_called()


def test_un_lien_d_activation_ne_sert_pas_a_reinitialiser(clean_db, courriel):
    client.post("/api/clients/inscription", json={"email": "jeanne@test.com"})

    res = client.post("/api/clients/reinitialiser", json={"token": _jeton_dans(courriel), "mot_de_passe": MDP})

    assert res.status_code == 400


# ---------- mon compte ----------

def test_moi_liste_mes_demandes_et_seulement_les_miennes(clean_db, courriel):
    miennes = _demande(clean_db)
    _demande(clean_db, "paul@test.com")
    token = _compte_actif(clean_db, courriel)

    res = client.get("/api/clients/moi", headers=_auth(token))

    assert res.status_code == 200
    corps = res.json()
    assert corps["email"] == "jeanne@test.com" and "password_hash" not in corps
    assert [d["id"] for d in corps["demandes"]] == [miennes["id"]]
    assert corps["demandes"][0]["jeton"] == miennes["jeton"] and corps["demandes"][0]["statut"] == "nouvelle"


def test_moi_exige_un_jeton_client(clean_db, courriel):
    assert client.get("/api/clients/moi").status_code == 401
    assert client.get("/api/clients/moi", headers=_auth("n-importe-quoi")).status_code == 401


def test_les_roles_sont_etanches(clean_db, courriel):
    jeton_client = _compte_actif(clean_db, courriel)
    clean_db.add(Admin(email="admin@test.com", password_hash=auth_service.hash_password("test-password-123")))
    clean_db.commit()
    jeton_admin = auth_service.login(clean_db, "admin@test.com", "test-password-123")

    # a customer can never act as the admin...
    assert client.get("/api/demandes", headers=_auth(jeton_client)).status_code == 401
    assert client.get("/api/teintes", headers=_auth(jeton_client)).status_code == 401
    assert client.post("/api/reglages-devis", headers=_auth(jeton_client)).status_code in (401, 405)
    # ...and the admin token is not a customer's
    assert client.get("/api/clients/moi", headers=_auth(jeton_admin)).status_code == 401
    assert client.get("/api/demandes", headers=_auth(jeton_admin)).status_code == 200


def test_supprimer_son_compte_garde_les_demandes(clean_db, courriel):
    demande = _demande(clean_db)
    token = _compte_actif(clean_db, courriel)

    mauvais = client.post("/api/clients/moi/supprimer", json={"mot_de_passe": "faux-mot-de-passe"}, headers=_auth(token))
    ok = client.post("/api/clients/moi/supprimer", json={"mot_de_passe": MDP}, headers=_auth(token))

    assert mauvais.status_code == 401 and ok.status_code == 204
    assert clean_db.query(Client).count() == 0
    assert clean_db.query(Demande).get(demande["id"]).client_id is None  # kept: the order history of the workshop
    assert client.get("/api/clients/moi", headers=_auth(token)).status_code == 401
