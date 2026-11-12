import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import email_service, paiement_service, stripe_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/stripe", tags=["Paiement"])


@router.post(
    "/webhook",
    summary="Webhook Stripe (signature obligatoire)",
    responses={400: {"description": "Signature absente ou invalide"}},
)
async def webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    payload = await request.body()
    try:
        evenement = stripe_service.verifier_evenement(payload, request.headers.get("stripe-signature"))
    except stripe_service.SignatureInvalideError:
        raise HTTPException(status_code=400, detail="Signature invalide")

    # Always answer 200 once the signature is good: Stripe would otherwise retry for days.
    demande = paiement_service.confirmer(db, evenement)
    if demande is not None:
        try:
            background_tasks.add_task(email_service.envoyer, email_service.messages_paiement_recu(demande))
        except KeyError:
            logger.exception("E-mails de paiement non envoyés (variable EMAIL_* manquante)")
    return {"recu": True}
