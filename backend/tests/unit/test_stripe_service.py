import hashlib
import hmac
import json
import time
from unittest.mock import patch

import pytest

from app.services import stripe_service

LIGNES = [
    {"nom": "Table basse · Charcoal", "montant_centimes": 25000, "quantite": 2},
    {"nom": "Livraison", "montant_centimes": 4000, "quantite": 1},
]


@pytest.fixture(autouse=True)
def cles(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_123")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")


def _signer(payload: bytes, secret="whsec_test", horodatage=None):
    t = horodatage or int(time.time())
    signature = hmac.new(secret.encode(), f"{t}.".encode() + payload, hashlib.sha256).hexdigest()
    return f"t={t},v1={signature}"


def test_creer_session_envoie_une_ligne_par_piece_en_euros_et_les_metadonnees():
    with patch("app.services.stripe_service.stripe.checkout.Session.create") as creer:
        creer.return_value = {"id": "cs_test_1", "url": "https://checkout.stripe.test/cs_test_1"}

        identifiant, url = stripe_service.creer_session(
            demande_id=42, jeton="abc", email="jeanne@test.com", lignes=LIGNES,
            expire_at=None, site_url="https://maison.test",
        )

    assert (identifiant, url) == ("cs_test_1", "https://checkout.stripe.test/cs_test_1")
    (_, kwargs) = creer.call_args
    assert kwargs["mode"] == "payment" and kwargs["customer_email"] == "jeanne@test.com"
    assert kwargs["metadata"] == {"demande_id": "42"}
    assert kwargs["payment_intent_data"] == {"metadata": {"demande_id": "42"}}
    assert kwargs["success_url"] == "https://maison.test/devis/abc?paiement=ok"
    assert kwargs["cancel_url"] == "https://maison.test/devis/abc?paiement=annule"
    assert kwargs["api_key"] == "sk_test_123"
    assert kwargs["line_items"] == [
        {"quantity": 2, "price_data": {"currency": "eur", "unit_amount": 25000, "product_data": {"name": "Table basse · Charcoal"}}},
        {"quantity": 1, "price_data": {"currency": "eur", "unit_amount": 4000, "product_data": {"name": "Livraison"}}},
    ]


def test_creer_session_borne_l_expiration_a_la_fenetre_acceptee_par_stripe():
    with patch("app.services.stripe_service.stripe.checkout.Session.create") as creer:
        creer.return_value = {"id": "cs", "url": "u"}
        bientot = int(time.time()) + 60          # quote expires in a minute: Stripe needs >= 30 min
        loin = int(time.time()) + 10 * 86400     # quote valid 10 days: Stripe allows 24 h at most
        stripe_service.creer_session(1, "j", "a@b.c", LIGNES, expire_at=bientot, site_url="https://x")
        stripe_service.creer_session(1, "j", "a@b.c", LIGNES, expire_at=loin, site_url="https://x")

    maintenant = time.time()
    premier, second = (appel.kwargs["expires_at"] for appel in creer.call_args_list)
    assert 1800 <= premier - maintenant <= 1900
    assert 85000 <= second - maintenant <= 86400


def test_creer_session_traduit_une_panne_stripe():
    import stripe

    with patch("app.services.stripe_service.stripe.checkout.Session.create", side_effect=stripe.APIConnectionError("réseau")):
        with pytest.raises(stripe_service.StripeIndisponibleError):
            stripe_service.creer_session(1, "j", "a@b.c", LIGNES, expire_at=None, site_url="https://x")


def test_rembourser_demande_le_remboursement_total_du_paiement():
    with patch("app.services.stripe_service.stripe.Refund.create") as rembourser:
        stripe_service.rembourser("pi_123")

    assert rembourser.call_args.kwargs["payment_intent"] == "pi_123"
    assert rembourser.call_args.kwargs["api_key"] == "sk_test_123"


def test_rembourser_traduit_une_panne_stripe():
    import stripe

    with patch("app.services.stripe_service.stripe.Refund.create", side_effect=stripe.InvalidRequestError("déjà remboursé", "pi")):
        with pytest.raises(stripe_service.StripeIndisponibleError):
            stripe_service.rembourser("pi_123")


def test_verifier_evenement_accepte_une_signature_valide_et_renvoie_un_dict():
    payload = json.dumps({"id": "evt_1", "object": "event", "type": "checkout.session.completed", "data": {"object": {"id": "cs_1"}}}).encode()

    evenement = stripe_service.verifier_evenement(payload, _signer(payload))

    assert evenement["type"] == "checkout.session.completed"
    assert evenement["data"]["object"]["id"] == "cs_1"


@pytest.mark.parametrize("cas", ["mauvais_secret", "sans_en_tete", "payload_modifie", "trop_ancien"])
def test_verifier_evenement_refuse_une_signature_invalide(cas):
    payload = b'{"id": "evt_1", "object": "event", "type": "x", "data": {"object": {}}}'
    en_tete = {
        "mauvais_secret": _signer(payload, secret="whsec_autre"),
        "sans_en_tete": None,
        "payload_modifie": _signer(b'{"autre": 1}'),
        "trop_ancien": _signer(payload, horodatage=int(time.time()) - 3600),
    }[cas]

    with pytest.raises(stripe_service.SignatureInvalideError):
        stripe_service.verifier_evenement(payload, en_tete)
