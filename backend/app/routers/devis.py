from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.devis import DevisIn, DevisOut
from app.services import commande_service, devis_service, email_service, parametre_service

router = APIRouter(prefix="/api/devis", tags=["Devis"])


@router.post(
    "",
    response_model=DevisOut,
    status_code=201,
    summary="Envoyer une demande de devis",
    responses={422: {"description": "Données invalides ou produit introuvable"}},
)
def create_devis(
    payload: DevisIn,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        devis = devis_service.create(db, payload.model_dump())
    except commande_service.ProduitIntrouvableError as erreur:
        raise HTTPException(status_code=422, detail=f"Produit n°{erreur.produit_id} introuvable")

    if parametre_service.get(db).email_commande_actif:
        try:
            messages = email_service.messages_nouveau_devis(devis)
        except KeyError:
            messages = []
        if messages:
            background_tasks.add_task(email_service.envoyer, messages)
    return devis
