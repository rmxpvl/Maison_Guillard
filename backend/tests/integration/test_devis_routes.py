from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.admin import Admin
from app.models.categorie import Categorie
from app.models.devis import Devis
from app.models.parametre import Parametre
from app.models.produit import Disponibilite, Produit
from app.services import auth_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()
    for modele in (Devis, Parametre, Produit, Categorie, Admin):
        db.query(modele).delete()
    db.commit()
    yield db
    for modele in (Devis, Parametre, Produit, Categorie, Admin):
        db.query(modele).delete()
    db.commit()
    db.close()


@pytest.fixture
def smtp_env(monkeypatch):
    for nom, valeur in {
        "SMTP_HOST": "smtp.test", "SMTP_PORT": "587", "SMTP_USER": "user@test.com",
        "SMTP_PASSWORD": "secret", "EMAIL_EXPEDITEUR": "site@test.com",
        "EMAIL_ARTISAN": "artisan@test.com",
    }.items():
        monkeypatch.setenv(nom, valeur)


def _produit(db, disponibilite=Disponibilite.sur_commande):
    categorie = Categorie(nom="Tables", slug="tables")
    db.add(categorie)
    db.commit()
    produit = Produit(
        nom="Table en frêne", description="Sur mesure", categorie_id=categorie.id,
        prix=1200, dimensions="200x90x75cm", disponibilite=disponibilite,
    )
    db.add(produit)
    db.commit()
    db.refresh(produit)
    return produit


def _corps(**changes):
    corps = {
        "nom_client": "Jeanne Martin",
        "email": "jeanne@test.com",
        "description_projet": "Une table de 2 mètres pour 8 personnes, en chêne clair.",
    }
    corps.update(changes)
    return corps


def _activer_email(db, actif):
    db.add(Parametre(email_commande_actif=actif))
    db.commit()


def test_post_devis_sans_produit(clean_db):
    res = client.post("/api/devis", json=_corps())

    assert res.status_code == 201
    body = res.json()
    assert body["statut"] == "nouveau"
    assert body["produit_id"] is None
    assert clean_db.query(Devis).count() == 1


def test_post_devis_pour_un_produit_sur_commande(clean_db):
    produit = _produit(clean_db)

    res = client.post("/api/devis", json=_corps(produit_id=produit.id))

    assert res.status_code == 201
    assert res.json()["produit_id"] == produit.id


def test_post_devis_refuse_un_produit_inconnu(clean_db):
    res = client.post("/api/devis", json=_corps(produit_id=999999))

    assert res.status_code == 422
    assert res.json()["detail"] == "Produit n°999999 introuvable"
    assert clean_db.query(Devis).count() == 0


def test_post_devis_refuse_une_description_trop_courte(clean_db):
    res = client.post("/api/devis", json=_corps(description_projet="court"))

    assert res.status_code == 422


def test_le_devis_reste_quand_son_produit_est_supprime(clean_db):
    produit = _produit(clean_db)
    devis_id = client.post("/api/devis", json=_corps(produit_id=produit.id)).json()["id"]
    clean_db.add(Admin(email="admin@test.com", password_hash=auth_service.hash_password("test-password-123")))
    clean_db.commit()
    token = auth_service.login(clean_db, "admin@test.com", "test-password-123")

    res = client.delete(f"/api/produits/{produit.id}", headers={"Authorization": f"Bearer {token}"})

    assert res.status_code == 204
    clean_db.expire_all()  # reload from the database: PostgreSQL changed the row itself
    devis = clean_db.get(Devis, devis_id)
    assert devis is not None
    assert devis.produit_id is None


def test_aucun_email_quand_le_reglage_est_desactive(clean_db, smtp_env):
    _activer_email(clean_db, False)

    with patch("app.services.email_service.smtplib.SMTP") as smtp:
        res = client.post("/api/devis", json=_corps())

    assert res.status_code == 201
    smtp.assert_not_called()


def test_deux_emails_quand_le_reglage_est_active(clean_db, smtp_env):
    _activer_email(clean_db, True)

    with patch("app.services.email_service.smtplib.SMTP") as smtp:
        res = client.post("/api/devis", json=_corps())

    assert res.status_code == 201
    assert smtp.return_value.__enter__.return_value.send_message.call_count == 2


def test_devis_cree_meme_si_le_serveur_smtp_est_injoignable(clean_db, smtp_env):
    _activer_email(clean_db, True)

    with patch("app.services.email_service.smtplib.SMTP", side_effect=OSError("réseau coupé")):
        res = client.post("/api/devis", json=_corps())

    assert res.status_code == 201
    assert clean_db.query(Devis).count() == 1
