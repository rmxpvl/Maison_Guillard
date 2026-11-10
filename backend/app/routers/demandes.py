from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.require_admin import require_admin
from app.models.demande import StatutDemande
from app.routers.reponses import NON_AUTORISE
from app.schemas.demande import (
    DemandeIn,
    DemandeOut,
    DemandePubliqueOut,
    ProjetLibreIn,
    StatutDemandeIn,
)
from app.services import demande_service, email_service

router = APIRouter(prefix="/api/demandes", tags=["Demandes"])

DEMANDE_INTROUVABLE = {404: {"description": "Demande introuvable"}}


def _prevenir(background_tasks: BackgroundTasks, demande) -> None:
    try:
        messages = email_service.messages_nouvelle_demande(demande)
    except KeyError:
        # A missing EMAIL_* variable must not cancel the request either.
        return
    background_tasks.add_task(email_service.envoyer, messages)


@router.post(
    "",
    response_model=DemandeOut,
    status_code=201,
    summary="Envoyer une demande (pièces du catalogue)",
    responses={422: {"description": "Données invalides, produit introuvable ou masqué, finition non proposée"}},
)
def create_demande(
    payload: DemandeIn,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        demande = demande_service.create(db, payload.model_dump())
    except demande_service.ProduitIntrouvableError as erreur:
        raise HTTPException(status_code=422, detail=f"Produit n°{erreur.produit_id} introuvable")
    except demande_service.ProduitMasqueError as erreur:
        raise HTTPException(status_code=422, detail=f"« {erreur.nom} » n'est plus disponible")
    except demande_service.TeinteNonProposeeError as erreur:
        raise HTTPException(status_code=422, detail=f"Cette finition n'est pas proposée pour « {erreur.nom} »")
    _prevenir(background_tasks, demande)
    return demande


@router.post(
    "/projet-libre",
    response_model=DemandeOut,
    status_code=201,
    summary="Envoyer un projet libre (sans pièce du catalogue)",
    responses={422: {"description": "Données invalides ou produit de référence introuvable"}},
)
def create_projet_libre(
    payload: ProjetLibreIn,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        demande = demande_service.create_projet_libre(db, payload.model_dump())
    except demande_service.ProduitIntrouvableError as erreur:
        raise HTTPException(status_code=422, detail=f"Produit n°{erreur.produit_id} introuvable")
    _prevenir(background_tasks, demande)
    return demande


@router.get(
    "/suivi/{jeton}",
    response_model=DemandePubliqueOut,
    summary="Voir sa demande avec le lien secret reçu par e-mail",
    responses=DEMANDE_INTROUVABLE,
)
def suivi_demande(jeton: str, db: Session = Depends(get_db)):
    demande = demande_service.get_by_jeton(db, jeton)
    if demande is None:
        raise HTTPException(status_code=404, detail="Demande introuvable")
    return demande


@router.get(
    "",
    response_model=list[DemandeOut],
    summary="Lister les demandes (les plus récentes d'abord)",
    responses=NON_AUTORISE,
)
def list_demandes(
    statut: StatutDemande | None = None,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    return demande_service.get_all(db, statut)


@router.get(
    "/{demande_id}",
    response_model=DemandeOut,
    summary="Voir une demande",
    responses={**NON_AUTORISE, **DEMANDE_INTROUVABLE},
)
def get_demande(
    demande_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    demande = demande_service.get_by_id(db, demande_id)
    if demande is None:
        raise HTTPException(status_code=404, detail="Demande introuvable")
    return demande


@router.patch(
    "/{demande_id}/statut",
    response_model=DemandeOut,
    summary="Changer le statut d'une demande (transitions contrôlées)",
    responses={
        **NON_AUTORISE,
        **DEMANDE_INTROUVABLE,
        409: {"description": "Ce changement de statut n'est pas possible"},
    },
)
def update_statut_demande(
    demande_id: int,
    payload: StatutDemandeIn,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    try:
        demande = demande_service.changer_statut(db, demande_id, payload.statut)
    except demande_service.TransitionInterditeError:
        raise HTTPException(status_code=409, detail="Ce changement de statut n'est pas possible")
    if demande is None:
        raise HTTPException(status_code=404, detail="Demande introuvable")
    return demande
