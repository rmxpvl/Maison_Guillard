from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.require_admin import require_admin
from app.models.devis import StatutDevis
from app.routers.reponses import NON_AUTORISE
from app.schemas.devis import DevisIn, DevisOut, StatutDevisIn
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


@router.get(
    "",
    response_model=list[DevisOut],
    summary="Lister les demandes de devis (les plus récentes d'abord)",
    responses=NON_AUTORISE,
)
def list_devis(
    statut: StatutDevis | None = None,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    return devis_service.get_all(db, statut)


@router.patch(
    "/{devis_id}/statut",
    response_model=DevisOut,
    summary="Changer le statut d'une demande de devis",
    responses={**NON_AUTORISE, 404: {"description": "Devis introuvable"}},
)
def update_statut_devis(
    devis_id: int,
    payload: StatutDevisIn,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    devis = devis_service.update_statut(db, devis_id, payload.statut)
    if devis is None:
        raise HTTPException(status_code=404, detail="Devis introuvable")
    return devis
