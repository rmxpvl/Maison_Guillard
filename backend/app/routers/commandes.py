from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.require_admin import require_admin
from app.models.commande import StatutCommande
from app.routers.reponses import NON_AUTORISE
from app.schemas.commande import CommandeIn, CommandeOut, StatutCommandeIn
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


@router.get(
    "",
    response_model=list[CommandeOut],
    summary="Lister les commandes (les plus récentes d'abord)",
    responses=NON_AUTORISE,
)
def list_commandes(
    statut: StatutCommande | None = None,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    return commande_service.get_all(db, statut)


@router.patch(
    "/{commande_id}/statut",
    response_model=CommandeOut,
    summary="Changer le statut d'une commande",
    responses={**NON_AUTORISE, 404: {"description": "Commande introuvable"}},
)
def update_statut_commande(
    commande_id: int,
    payload: StatutCommandeIn,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    commande = commande_service.update_statut(db, commande_id, payload.statut)
    if commande is None:
        raise HTTPException(status_code=404, detail="Commande introuvable")
    return commande