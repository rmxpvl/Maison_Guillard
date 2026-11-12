import logging
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.demande import Demande, StatutDemande
from app.services import demande_service, stripe_service

logger = logging.getLogger(__name__)

CGV_VERSION = "1"
DELAI_LIVRAISON = timedelta(days=15)  # manufacture + delivery guaranteed after payment
STATUTS_REMBOURSABLES_ARTISANE = {StatutDemande.payee, StatutDemande.en_fabrication}


class DevisNonPayableError(Exception):
    """The quote is missing, expired, refused or already paid."""


class AnnulationImpossibleError(Exception):
    pass


def _centimes(montant: Decimal) -> int:
    return int((montant * 100).to_integral_value())


def lignes_stripe(demande: Demande) -> list[dict]:
    """One Stripe line per piece (final price x quantity) plus delivery, amounts read from the
    database. A line priced 0 is skipped: Stripe needs positive amounts."""
    lignes = []
    for l in demande.lignes:
        centimes = _centimes(l.prix_final or Decimal("0"))
        if centimes > 0:
            nom = l.libelle + (f" · {l.teinte_nom}" if l.teinte_nom else "")
            lignes.append({"nom": nom, "montant_centimes": centimes, "quantite": l.quantite})
    frais = _centimes(demande.frais_livraison or Decimal("0"))
    if frais > 0:
        lignes.append({"nom": "Livraison", "montant_centimes": frais, "quantite": 1})
    return lignes


def total_centimes(demande: Demande) -> int:
    return sum(l["montant_centimes"] * l["quantite"] for l in lignes_stripe(demande))


def demarrer(db: Session, jeton: str) -> str | None:
    """Customer clicks « Accepter et payer » (CGV box ticked): returns the Stripe page URL.
    The CGV acceptance is saved only once Stripe has created the session."""
    demande = demande_service.get_by_jeton(db, jeton)
    if demande is None:
        return None
    if demande.statut != StatutDemande.devis_envoye:
        raise DevisNonPayableError()
    lignes = lignes_stripe(demande)
    if not lignes:
        raise DevisNonPayableError()

    identifiant, url = stripe_service.creer_session(
        demande_id=demande.id,
        jeton=demande.jeton,
        email=demande.email,
        lignes=lignes,
        expire_at=demande.expire_at,
        site_url=os.environ.get("SITE_URL", "http://localhost:5173"),
    )
    demande.stripe_session_id = identifiant
    demande.cgv_acceptees_at = datetime.now(timezone.utc)
    demande.cgv_version = CGV_VERSION
    db.commit()
    return url


def confirmer(db: Session, evenement: dict) -> Demande | None:
    """Webhook: marks the request paid. Returns it only when it has just been marked paid (so the
    caller sends the e-mails once). Idempotent, and it never trusts an amount it cannot match."""
    if evenement.get("type") != "checkout.session.completed":
        return None
    session = evenement["data"]["object"]
    if session.get("payment_status") != "paid":
        return None
    try:
        demande_id = int(session["metadata"]["demande_id"])
    except (KeyError, TypeError, ValueError):
        logger.error("Paiement Stripe %s sans demande_id", session.get("id"))
        return None

    demande = db.query(Demande).filter(Demande.id == demande_id).with_for_update().first()
    if demande is None:
        logger.error("Paiement Stripe %s pour une demande inconnue (%s)", session.get("id"), demande_id)
        return None
    if demande.payee_at is not None:
        return None  # same event received twice
    if demande.statut != StatutDemande.devis_envoye:
        logger.error("Paiement Stripe %s reçu pour la demande %s au statut %s : à traiter à la main",
                     session.get("id"), demande.id, demande.statut.value)
        return None
    if session.get("id") != demande.stripe_session_id:
        logger.error("Paiement Stripe %s : ce n'est pas la session en cours de la demande %s", session.get("id"), demande.id)
        return None
    if session.get("amount_total") != total_centimes(demande):
        logger.error("Paiement Stripe %s : montant %s différent du devis (%s) de la demande %s",
                     session.get("id"), session.get("amount_total"), total_centimes(demande), demande.id)
        return None

    maintenant = datetime.now(timezone.utc)
    demande.statut = StatutDemande.payee
    demande.payee_at = maintenant
    demande.date_limite = maintenant + DELAI_LIVRAISON
    demande.montant_paye = Decimal(session["amount_total"]) / 100
    demande.stripe_payment_intent_id = session.get("payment_intent")
    db.commit()
    db.refresh(demande)
    return demande


def _rembourser(db: Session, demande: Demande, autorises: set[StatutDemande]) -> Demande:
    db.refresh(demande, with_for_update=True)  # two clicks at once refund only once
    if demande.statut not in autorises or not demande.stripe_payment_intent_id:
        raise AnnulationImpossibleError()
    stripe_service.rembourser(demande.stripe_payment_intent_id)  # a Stripe failure leaves the status alone
    demande.statut = StatutDemande.annulee
    demande.rembourse_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(demande)
    return demande


def annuler_par_le_client(db: Session, jeton: str) -> Demande | None:
    """Paid and not yet in manufacture: full refund. Later, the customer contacts the workshop."""
    demande = demande_service.get_by_jeton(db, jeton)
    if demande is None:
        return None
    return _rembourser(db, demande, {StatutDemande.payee})


def rembourser_par_l_artisane(db: Session, demande_id: int) -> Demande | None:
    demande = demande_service.get_by_id(db, demande_id)
    if demande is None:
        return None
    return _rembourser(db, demande, STATUTS_REMBOURSABLES_ARTISANE)
