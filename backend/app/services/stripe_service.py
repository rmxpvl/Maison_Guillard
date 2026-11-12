import json
import os
import time
from datetime import datetime

import stripe

# Thin adapter over the Stripe SDK: the rest of the app never imports `stripe`, and tests replace
# these three functions. Stripe Checkout is hosted by Stripe: no card data ever reaches the site.

# Stripe accepts a Checkout Session that expires between 30 minutes and 24 hours from now.
EXPIRATION_MIN = 30 * 60 + 60
EXPIRATION_MAX = 24 * 3600 - 60


class StripeIndisponibleError(Exception):
    """Stripe could not be reached or refused the request (or is not configured)."""


class SignatureInvalideError(Exception):
    """A webhook whose Stripe signature is missing, wrong or too old."""


def _cle() -> str:
    cle = os.environ.get("STRIPE_SECRET_KEY")
    if not cle:
        raise StripeIndisponibleError("STRIPE_SECRET_KEY manquante")
    return cle


def _expiration(expire_at) -> int:
    """The quote's expiry, squeezed into the window Stripe accepts."""
    maintenant = int(time.time())
    if isinstance(expire_at, datetime):
        expire_at = int(expire_at.timestamp())
    souhaitee = expire_at if expire_at is not None else maintenant + EXPIRATION_MAX
    return max(maintenant + EXPIRATION_MIN, min(souhaitee, maintenant + EXPIRATION_MAX))


def creer_session(demande_id, jeton, email, lignes, expire_at, site_url) -> tuple[str, str]:
    """Creates the Checkout Session. `lignes`: [{nom, montant_centimes, quantite}], amounts read
    from the database by the caller. Returns (session id, payment page URL)."""
    cle = _cle()
    try:
        session = stripe.checkout.Session.create(
            api_key=cle,
            mode="payment",
            locale="fr",
            customer_email=email,
            client_reference_id=str(demande_id),
            metadata={"demande_id": str(demande_id)},
            payment_intent_data={"metadata": {"demande_id": str(demande_id)}},
            line_items=[
                {
                    "quantity": ligne["quantite"],
                    "price_data": {
                        "currency": "eur",
                        "unit_amount": ligne["montant_centimes"],
                        "product_data": {"name": ligne["nom"]},
                    },
                }
                for ligne in lignes
            ],
            success_url=f"{site_url.rstrip('/')}/devis/{jeton}?paiement=ok",
            cancel_url=f"{site_url.rstrip('/')}/devis/{jeton}?paiement=annule",
            expires_at=_expiration(expire_at),
        )
        return session["id"], session["url"]
    except stripe.StripeError as erreur:
        raise StripeIndisponibleError(str(erreur)) from erreur


def rembourser(payment_intent_id: str) -> None:
    """Full refund of a payment."""
    cle = _cle()
    try:
        stripe.Refund.create(api_key=cle, payment_intent=payment_intent_id)
    except stripe.StripeError as erreur:
        raise StripeIndisponibleError(str(erreur)) from erreur


def verifier_evenement(payload: bytes, en_tete_signature: str | None) -> dict:
    """Checks the webhook signature (STRIPE_WEBHOOK_SECRET) and returns the event as a plain dict."""
    secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    if not secret or not en_tete_signature:
        raise SignatureInvalideError()
    try:
        stripe.Webhook.construct_event(payload, en_tete_signature, secret)
    except (ValueError, stripe.SignatureVerificationError) as erreur:
        raise SignatureInvalideError() from erreur
    return json.loads(payload)
