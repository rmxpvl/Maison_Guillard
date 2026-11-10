from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.require_admin import require_admin
from app.models.demande import StatutDemande
from app.routers.reponses import NON_AUTORISE
from app.schemas.demande import (
    DemandeIn,
    DevisIn,
    DemandeOut,
    DemandePubliqueOut,
    ProjetLibreIn,
    StatutDemandeIn,
)
from app.services import demande_service, devis_service, email_service, pdf_service, reglages_service

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


def _publique(db: Session, demande) -> DemandePubliqueOut:
    """Customer view, plus the workshop's contact details (« contactez l'atelier »)."""
    reglages = reglages_service.get(db)
    return DemandePubliqueOut.model_validate(demande).model_copy(
        update={
            "atelier_email": reglages.email or None,
            "atelier_telephone": reglages.telephone or None,
        }
    )


def _pdf(vue) -> Response:
    return Response(content=pdf_service.rendre_devis(vue), media_type="application/pdf")


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
    return _publique(db, demande)


@router.get(
    "/suivi/{jeton}/devis.pdf",
    summary="Télécharger le PDF du devis (lien secret)",
    responses={404: {"description": "Demande introuvable ou devis pas encore envoyé"}},
)
def suivi_devis_pdf(jeton: str, db: Session = Depends(get_db)):
    demande = demande_service.get_by_jeton(db, jeton)
    vue = devis_service.vue_depuis_demande(demande) if demande else None
    if vue is None:
        raise HTTPException(status_code=404, detail="Devis introuvable")
    return _pdf(vue)


@router.post(
    "/suivi/{jeton}/refuser",
    response_model=DemandePubliqueOut,
    summary="Refuser le devis (lien secret)",
    responses={**DEMANDE_INTROUVABLE, 409: {"description": "Le devis ne peut plus être refusé"}},
)
def refuser_devis(jeton: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        demande = devis_service.refuser(db, jeton)
    except devis_service.StatutDevisInterditError:
        raise HTTPException(status_code=409, detail="Ce devis ne peut plus être refusé")
    if demande is None:
        raise HTTPException(status_code=404, detail="Demande introuvable")
    try:
        background_tasks.add_task(email_service.envoyer, email_service.messages_devis_refuse(demande))
    except KeyError:
        pass  # a missing EMAIL_* variable must not undo the refusal
    return _publique(db, demande)


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
    suggere = reglages_service.frais_par_defaut(
        demande_service.univers_de(db, demande), reglages_service.get(db)
    )
    return DemandeOut.model_validate(demande).model_copy(update={"frais_livraison_suggere": suggere})


@router.post(
    "/{demande_id}/devis",
    response_model=DemandeOut,
    summary="Envoyer (ou renvoyer) le devis au client",
    responses={
        **NON_AUTORISE,
        **DEMANDE_INTROUVABLE,
        409: {"description": "La demande est déjà payée ou terminée"},
        422: {"description": "Réglages du devis incomplets ou lignes invalides"},
    },
)
def envoyer_devis(
    demande_id: int,
    payload: DevisIn,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    try:
        demande = devis_service.envoyer(db, demande_id, payload.model_dump())
    except devis_service.StatutDevisInterditError:
        raise HTTPException(status_code=409, detail="Ce devis ne peut plus être modifié")
    except devis_service.ReglagesIncompletsError as erreur:
        raise HTTPException(
            status_code=422, detail="Réglages du devis incomplets : " + ", ".join(erreur.manquants)
        )
    except devis_service.LigneDevisInvalideError as erreur:
        raise HTTPException(status_code=422, detail=str(erreur))
    if demande is None:
        raise HTTPException(status_code=404, detail="Demande introuvable")
    pdf = pdf_service.rendre_devis(devis_service.vue_depuis_demande(demande))
    try:
        background_tasks.add_task(email_service.envoyer, email_service.messages_devis(demande, pdf))
    except KeyError:
        pass  # the admin page also shows the link to copy
    return demande


@router.post(
    "/{demande_id}/devis/apercu",
    summary="Aperçu PDF du devis en cours d'édition (rien n'est enregistré)",
    responses={**NON_AUTORISE, **DEMANDE_INTROUVABLE, 422: {"description": "Lignes invalides"}},
)
def apercu_devis(
    demande_id: int,
    payload: DevisIn,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    try:
        vue = devis_service.apercu(db, demande_id, payload.model_dump())
    except devis_service.LigneDevisInvalideError as erreur:
        raise HTTPException(status_code=422, detail=str(erreur))
    if vue is None:
        raise HTTPException(status_code=404, detail="Demande introuvable")
    return _pdf(vue)


@router.get(
    "/{demande_id}/devis.pdf",
    summary="Télécharger le PDF du devis envoyé",
    responses={**NON_AUTORISE, 404: {"description": "Demande introuvable ou devis pas encore envoyé"}},
)
def devis_pdf(demande_id: int, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    demande = demande_service.get_by_id(db, demande_id)
    vue = devis_service.vue_depuis_demande(demande) if demande else None
    if vue is None:
        raise HTTPException(status_code=404, detail="Devis introuvable")
    return _pdf(vue)


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
