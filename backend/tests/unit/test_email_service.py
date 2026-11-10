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
    monkeypatch.setenv("SITE_URL", "https://maison.test")


def _demande(**extra):
    ligne = MagicMock(libelle="Table basse", quantite=2, prix_indicatif=Decimal("199.99"),
                      teinte_nom="Charcoal", souhait="Plus haute")
    base = dict(
        id=42, jeton="abc123", nom_client="Jeanne Martin", email="jeanne@test.com", telephone=None,
        adresse="1 rue du Bois", message_client=None, description_projet=None,
        lignes=[ligne], total_indicatif=Decimal("399.98"),
    )
    base.update(extra)
    return MagicMock(**base)


def test_messages_pour_l_artisane_et_le_client():
    artisan, client = email_service.messages_nouvelle_demande(_demande())

    assert artisan["To"] == "artisan@test.com"
    assert artisan["Subject"] == "Nouvelle demande n°42"
    assert "Table basse x 2" in artisan.get_content()
    assert "Charcoal" in artisan.get_content() and "Plus haute" in artisan.get_content()
    assert client["To"] == "jeanne@test.com"
    assert "48 h" in client.get_content()
    assert "https://maison.test/devis/abc123" in client.get_content()


def test_message_d_un_projet_libre_contient_la_description():
    artisan, _ = email_service.messages_nouvelle_demande(
        _demande(lignes=[], description_projet="Une table de 3 mètres en frêne")
    )

    assert "Une table de 3 mètres en frêne" in artisan.get_content()


def test_envoyer_passe_par_smtp_avec_starttls():
    with patch("app.services.email_service.smtplib.SMTP") as smtp:
        email_service.envoyer(email_service.messages_nouvelle_demande(_demande()))

    serveur = smtp.return_value.__enter__.return_value
    serveur.starttls.assert_called_once()
    serveur.login.assert_called_once_with("user@test.com", "secret")
    assert serveur.send_message.call_count == 2


def test_envoyer_ne_leve_jamais_d_erreur():
    with patch("app.services.email_service.smtplib.SMTP", side_effect=OSError("réseau coupé")):
        email_service.envoyer(email_service.messages_nouvelle_demande(_demande()))
