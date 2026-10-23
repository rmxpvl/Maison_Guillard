from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.commande import CommandeIn, CommandeOut
from app.services import commande_service, email_service, parametre_service

router = APIRouter(prefix="/api/commandes", tags=["Commandes"])


@router.post(
    "",
    response_model=CommandeOut,
    status_code=201,
    summary="Passer une commande",
    responses={422: {"description": "Données invalides, produit introuvable ou indisponible"}},
)
def create_commande(
    payload: CommandeIn,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        commande = commande_service.create(db, payload.model_dump())
    except commande_service.ProduitIntrouvableError as erreur:
        raise HTTPException(status_code=422, detail=f"Produit n°{erreur.produit_id} introuvable")
    except commande_service.ProduitIndisponibleError as erreur:
        raise HTTPException(status_code=422, detail=f"« {erreur.nom} » n'est plus disponible")

    if parametre_service.get(db).email_commande_actif:
        try:
            messages = email_service.messages_nouvelle_commande(commande)
        except KeyError:
            # A missing EMAIL_* variable must not cancel the order either.
            messages = []
        if messages:
            background_tasks.add_task(email_service.envoyer, messages)
    return commande
