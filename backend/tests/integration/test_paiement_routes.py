import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.admin import Admin
from app.models.categorie import Categorie, Univers
from app.models.demande import Demande, StatutDemande
from app.models.devis_numero import CompteurDevis
from app.models.message_type import MessageType
from app.models.parametre import Parametre
from app.models.produit import Produit
from app.services import auth_service, stripe_service

client = TestClient(app)
CLIENT = {"nom_client": "Jeanne Martin", "email": "jeanne@test.com", "adresse": "1 rue du Bois"}
REGLAGES = {
    "nom_commercial": "Maison Guillard", "nom_legal": "EI Camille Guillard", "adresse": "3 rue de l'Atelier",
    "siret": "123 456 789 00012", "email": "atelier@test.com", "telephone": "04 00 00 00 00",
    "prenom_signature": "Camille", "mention_tva": "TVA non applicable", "validite_jours": 30,
    "frais_meubles": "0", "frais_ceramique": "0", "frais_papeterie": "0",
    "cond_paiement": "p", "cond_fabrication": "f", "cond_annulation": "a",
}
SECRET = "whsec_test"


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", SECRET)
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_123")
    monkeypatch.setenv("SITE_URL", "https://maison.test")
    monkeypatch.setenv("EMAIL_ARTISAN", "artisan@test.com")
    monkeypatch.setenv("EMAIL_EXPEDITEUR", "site@test.com")


@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()

    def vider():
        for modele in (Demande, Produit, Categorie, MessageType, Parametre, CompteurDevis, Admin):
            db.query(modele).delete()
        db.commit()

    vider()
    yield db
    vider()
    db.close()


@pytest.fixture(autouse=True)
def courriel():
    with patch("app.routers.demandes.email_service.envoyer") as envoi, patch("app.routers.stripe_webhook.email_service.envoyer", envoi):
        yield envoi


@pytest.fixture
def stripe_ok():
    with patch("app.services.paiement_service.stripe_service.creer_session", return_value=("cs_test_1", "https://checkout.stripe.test/cs_test_1")) as creer, \
         patch("app.services.paiement_service.stripe_service.rembourser") as rembourser:
        creer.rembourser = rembourser
        yield creer


@pytest.fixture
def admin(clean_db):
    clean_db.add(Admin(email="admin@test.com", password_hash=auth_service.hash_password("test-password-123")))
    clean_db.commit()
    return {"Authorization": f"Bearer {auth_service.login(clean_db, 'admin@test.com', 'test-password-123')}"}


def _devis_envoye(db, admin, prix="250.00", frais="40.00"):
    """A request whose quote has been sent: 2 x 250 + 40 = 540 EUR."""
    assert client.put("/api/reglages-devis", json=REGLAGES, headers=admin).status_code == 200
    categorie = Categorie(nom="Tables", slug="tables", univers=Univers.meubles)
    db.add(categorie)
    db.commit()
    produit = Produit(nom="Table basse", description="d", categorie_id=categorie.id, prix=200, dimensions="1x1")
    db.add(produit)
    db.commit()
    demande = client.post("/api/demandes", json={**CLIENT, "lignes": [{"produit_id": produit.id, "quantite": 2}]}).json()
    corps = {"lignes": [{"id": demande["lignes"][0]["id"], "prix_final": prix}], "lignes_libres": [],
             "frais_livraison": frais, "message_artisane": None}
    assert client.post(f"/api/demandes/{demande['id']}/devis", json=corps, headers=admin).status_code == 200
    return db.query(Demande).one()


def _evenement(demande, **extra):
    session = {"id": "cs_test_1", "object": "checkout.session", "payment_status": "paid",
               "amount_total": 54000, "payment_intent": "pi_1", "metadata": {"demande_id": str(demande.id)}}
    session.update(extra)
    return {"id": f"evt_{int(time.time() * 1000)}", "object": "event", "type": "checkout.session.completed", "data": {"object": session}}


def _webhook(evenement, secret=SECRET, signer=True):
    payload = json.dumps(evenement).encode()
    t = int(time.time())
    en_tete = {"Stripe-Signature": f"t={t},v1={hmac.new(secret.encode(), f'{t}.'.encode() + payload, hashlib.sha256).hexdigest()}"} if signer else {}
    return client.post("/api/stripe/webhook", content=payload, headers={**en_tete, "Content-Type": "application/json"})


def _payee(db, admin, stripe_ok, demande=None):
    demande = demande or _devis_envoye(db, admin)
    client.post(f"/api/demandes/suivi/{demande.jeton}/payer", json={"cgv_acceptees": True})
    assert _webhook(_evenement(demande)).status_code == 200
    db.refresh(demande)
    return demande


# ---------- accepter et payer ----------

def test_payer_cree_la_session_avec_les_montants_de_la_base_et_enregistre_les_cgv(clean_db, admin, stripe_ok):
    demande = _devis_envoye(clean_db, admin)

    res = client.post(f"/api/demandes/suivi/{demande.jeton}/payer", json={"cgv_acceptees": True})

    assert res.status_code == 200 and res.json() == {"url": "https://checkout.stripe.test/cs_test_1"}
    _, kwargs = stripe_ok.call_args
    assert kwargs["lignes"] == [
        {"nom": "Table basse", "montant_centimes": 25000, "quantite": 2},
        {"nom": "Livraison", "montant_centimes": 4000, "quantite": 1},
    ]
    assert kwargs["demande_id"] == demande.id and kwargs["email"] == "jeanne@test.com"
    clean_db.refresh(demande)
    assert demande.stripe_session_id == "cs_test_1" and demande.cgv_version == "1"
    assert demande.cgv_acceptees_at is not None


def test_payer_exige_la_case_des_cgv(clean_db, admin, stripe_ok):
    demande = _devis_envoye(clean_db, admin)

    assert client.post(f"/api/demandes/suivi/{demande.jeton}/payer", json={"cgv_acceptees": False}).status_code == 422
    assert client.post(f"/api/demandes/suivi/{demande.jeton}/payer", json={}).status_code == 422
    stripe_ok.assert_not_called()


def test_payer_refuse_un_devis_non_valide(clean_db, admin, stripe_ok):
    demande = _devis_envoye(clean_db, admin)
    demande.expire_at = datetime.now(timezone.utc) - timedelta(days=1)
    clean_db.commit()
    url = f"/api/demandes/suivi/{demande.jeton}/payer"

    assert client.post(url, json={"cgv_acceptees": True}).status_code == 409  # expired
    demande.statut = StatutDemande.nouvelle
    clean_db.commit()
    assert client.post(url, json={"cgv_acceptees": True}).status_code == 409  # no quote yet
    assert client.post("/api/demandes/suivi/inconnu/payer", json={"cgv_acceptees": True}).status_code == 404
    stripe_ok.assert_not_called()


def test_payer_si_stripe_est_en_panne_rien_n_est_enregistre(clean_db, admin):
    demande = _devis_envoye(clean_db, admin)
    with patch("app.services.paiement_service.stripe_service.creer_session", side_effect=stripe_service.StripeIndisponibleError()):
        res = client.post(f"/api/demandes/suivi/{demande.jeton}/payer", json={"cgv_acceptees": True})

    assert res.status_code == 502
    assert "paiement" in res.json()["detail"].lower()
    clean_db.refresh(demande)
    assert demande.cgv_acceptees_at is None and demande.stripe_session_id is None and demande.statut == StatutDemande.devis_envoye


# ---------- webhook ----------

def test_webhook_paiement_reussi_marque_payee_et_previent(clean_db, admin, stripe_ok, courriel):
    demande = _devis_envoye(clean_db, admin)
    client.post(f"/api/demandes/suivi/{demande.jeton}/payer", json={"cgv_acceptees": True})
    courriel.reset_mock()

    res = _webhook(_evenement(demande))

    assert res.status_code == 200
    clean_db.refresh(demande)
    assert demande.statut == StatutDemande.payee
    assert demande.stripe_payment_intent_id == "pi_1" and str(demande.montant_paye) == "540.00"
    assert demande.date_limite - demande.payee_at == timedelta(days=15)
    (messages,), _ = courriel.call_args
    assert sorted(m["To"] for m in messages) == ["artisan@test.com", "jeanne@test.com"]


def test_webhook_est_idempotent(clean_db, admin, stripe_ok, courriel):
    demande = _devis_envoye(clean_db, admin)
    client.post(f"/api/demandes/suivi/{demande.jeton}/payer", json={"cgv_acceptees": True})
    evenement = _evenement(demande)
    _webhook(evenement)
    clean_db.refresh(demande)
    premiere_date = demande.payee_at
    courriel.reset_mock()

    res = _webhook(evenement)

    assert res.status_code == 200
    courriel.assert_not_called()
    clean_db.refresh(demande)
    assert demande.payee_at == premiere_date


def test_webhook_signature_invalide_400(clean_db, admin, stripe_ok):
    demande = _devis_envoye(clean_db, admin)

    assert _webhook(_evenement(demande), secret="whsec_autre").status_code == 400
    assert _webhook(_evenement(demande), signer=False).status_code == 400
    clean_db.refresh(demande)
    assert demande.statut == StatutDemande.devis_envoye


@pytest.mark.parametrize("modif", [
    {"amount_total": 100},                  # amount does not match the quote
    {"payment_status": "unpaid"},           # not paid yet
    {"id": "cs_ancienne_session"},          # not the session of the current quote
])
def test_webhook_ne_marque_pas_payee_si_les_controles_echouent(clean_db, admin, stripe_ok, courriel, modif):
    demande = _devis_envoye(clean_db, admin)
    client.post(f"/api/demandes/suivi/{demande.jeton}/payer", json={"cgv_acceptees": True})
    courriel.reset_mock()

    res = _webhook(_evenement(demande, **modif))

    assert res.status_code == 200
    clean_db.refresh(demande)
    assert demande.statut == StatutDemande.devis_envoye
    courriel.assert_not_called()


def test_webhook_ignore_les_autres_evenements(clean_db, admin, stripe_ok):
    demande = _devis_envoye(clean_db, admin)
    evenement = {**_evenement(demande), "type": "charge.refunded"}

    assert _webhook(evenement).status_code == 200
    clean_db.refresh(demande)
    assert demande.statut == StatutDemande.devis_envoye


def test_webhook_demande_inconnue_ne_plante_pas(clean_db, admin, stripe_ok):
    demande = _devis_envoye(clean_db, admin)
    evenement = _evenement(demande, metadata={"demande_id": "999999"})

    assert _webhook(evenement).status_code == 200


def test_la_page_du_client_montre_la_date_limite_apres_paiement(clean_db, admin, stripe_ok):
    demande = _payee(clean_db, admin, stripe_ok)

    vu = client.get(f"/api/demandes/suivi/{demande.jeton}").json()

    assert vu["statut"] == "payee" and vu["payee_at"] and vu["date_limite"]
    pdf = client.get(f"/api/demandes/suivi/{demande.jeton}/devis.pdf")
    assert pdf.status_code == 200


# ---------- annulation et remboursement ----------

def test_le_client_annule_sa_commande_payee_et_est_rembourse(clean_db, admin, stripe_ok, courriel):
    demande = _payee(clean_db, admin, stripe_ok)
    courriel.reset_mock()

    res = client.post(f"/api/demandes/suivi/{demande.jeton}/annuler")

    assert res.status_code == 200 and res.json()["statut"] == "annulee" and res.json()["rembourse_at"]
    stripe_ok.rembourser.assert_called_once_with("pi_1")
    (messages,), _ = courriel.call_args
    assert sorted(m["To"] for m in messages) == ["artisan@test.com", "jeanne@test.com"]


def test_le_client_ne_peut_plus_annuler_une_fois_la_fabrication_commencee(clean_db, admin, stripe_ok):
    demande = _payee(clean_db, admin, stripe_ok)
    client.patch(f"/api/demandes/{demande.id}/statut", json={"statut": "en_fabrication"}, headers=admin)

    assert client.post(f"/api/demandes/suivi/{demande.jeton}/annuler").status_code == 409
    stripe_ok.rembourser.assert_not_called()


def test_annuler_sans_paiement_ou_deux_fois_409(clean_db, admin, stripe_ok):
    demande = _devis_envoye(clean_db, admin)
    assert client.post(f"/api/demandes/suivi/{demande.jeton}/annuler").status_code == 409
    assert client.post("/api/demandes/suivi/inconnu/annuler").status_code == 404

    payee = _payee(clean_db, admin, stripe_ok, demande)  # same request, now paid
    assert client.post(f"/api/demandes/suivi/{payee.jeton}/annuler").status_code == 200
    assert client.post(f"/api/demandes/suivi/{payee.jeton}/annuler").status_code == 409
    assert stripe_ok.rembourser.call_count == 1


def test_si_le_remboursement_echoue_le_statut_ne_change_pas(clean_db, admin, stripe_ok):
    demande = _payee(clean_db, admin, stripe_ok)
    stripe_ok.rembourser.side_effect = stripe_service.StripeIndisponibleError()

    res = client.post(f"/api/demandes/suivi/{demande.jeton}/annuler")

    assert res.status_code == 502
    assert "rembours" in res.json()["detail"].lower()
    clean_db.refresh(demande)
    assert demande.statut == StatutDemande.payee and demande.rembourse_at is None


@pytest.mark.parametrize("depart", [StatutDemande.payee, StatutDemande.en_fabrication])
def test_l_artisane_rembourse_une_commande_payee_ou_en_fabrication(clean_db, admin, stripe_ok, courriel, depart):
    demande = _payee(clean_db, admin, stripe_ok)
    demande.statut = depart
    clean_db.commit()
    courriel.reset_mock()

    res = client.post(f"/api/demandes/{demande.id}/rembourser", headers=admin)

    assert res.status_code == 200 and res.json()["statut"] == "annulee"
    stripe_ok.rembourser.assert_called_once_with("pi_1")
    (messages,), _ = courriel.call_args
    assert [m["To"] for m in messages] == ["jeanne@test.com"]


def test_l_artisane_ne_rembourse_pas_ce_qui_n_est_pas_paye_ou_est_expedie(clean_db, admin, stripe_ok):
    demande = _devis_envoye(clean_db, admin)
    assert client.post(f"/api/demandes/{demande.id}/rembourser", headers=admin).status_code == 409
    assert client.post("/api/demandes/999999/rembourser", headers=admin).status_code == 404

    payee = _payee(clean_db, admin, stripe_ok, demande)
    payee.statut = StatutDemande.expediee
    clean_db.commit()
    assert client.post(f"/api/demandes/{payee.id}/rembourser", headers=admin).status_code == 409


def test_marquer_expediee_previent_le_client(clean_db, admin, stripe_ok, courriel):
    demande = _payee(clean_db, admin, stripe_ok)
    client.patch(f"/api/demandes/{demande.id}/statut", json={"statut": "en_fabrication"}, headers=admin)
    courriel.reset_mock()

    res = client.patch(f"/api/demandes/{demande.id}/statut", json={"statut": "expediee"}, headers=admin)

    assert res.status_code == 200
    (messages,), _ = courriel.call_args
    assert [m["To"] for m in messages] == ["jeanne@test.com"]
    assert "expédiée" in messages[0]["Subject"]
