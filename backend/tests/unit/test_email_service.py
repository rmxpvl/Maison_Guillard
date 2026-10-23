from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services import email_service


@pytest.fixture(autouse=True)
def smtp_env(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.test")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "user@test.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret")
    monkeypatch.setenv("EMAIL_EXPEDITEUR", "site@test.com")
    monkeypatch.setenv("EMAIL_ARTISAN", "artisan@test.com")


def _commande():
    ligne = MagicMock(quantite=2, prix_unitaire_snapshot=Decimal("199.99"))
    ligne.produit.nom = "Table basse"
    return MagicMock(
        id=42, nom_client="Jeanne Martin", email="jeanne@test.com", telephone=None,
        adresse="1 rue du Bois", lignes=[ligne], total=Decimal("399.98"),
    )


def test_messages_pour_l_artisan_et_le_client():
    artisan, client = email_service.messages_nouvelle_commande(_commande())

    assert artisan["To"] == "artisan@test.com"
    assert artisan["Subject"] == "Nouvelle commande n°42"
    assert "Table basse x 2" in artisan.get_content()
    assert "399.98 €" in artisan.get_content()
    assert client["To"] == "jeanne@test.com"
    assert "48 h" in client.get_content()


def test_envoyer_passe_par_smtp_avec_starttls():
    with patch("app.services.email_service.smtplib.SMTP") as smtp:
        email_service.envoyer(email_service.messages_nouvelle_commande(_commande()))

    serveur = smtp.return_value.__enter__.return_value
    serveur.starttls.assert_called_once()
    serveur.login.assert_called_once_with("user@test.com", "secret")
    assert serveur.send_message.call_count == 2


def test_envoyer_ne_leve_jamais_d_erreur():
    with patch("app.services.email_service.smtplib.SMTP", side_effect=OSError("réseau coupé")):
        email_service.envoyer(email_service.messages_nouvelle_commande(_commande()))  # no exception
