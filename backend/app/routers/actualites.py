from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.require_admin import require_admin
from app.routers.reponses import NON_AUTORISE, STOCKAGE_INDISPONIBLE
from app.schemas.actualite import (
    ActualiteIn,
    ActualiteOut,
    ActualiteUpdate,
    LegendeIn,
    PhotoActualiteOut,
)
from app.services import actualite_service, photo_service

router = APIRouter(prefix="/api/actualites", tags=["Actualités"])

ACTUALITE_INTROUVABLE = {404: {"description": "Actualité introuvable"}}
PHOTO_INTROUVABLE = {404: {"description": "Photo introuvable"}}


@router.get("", response_model=list[ActualiteOut], summary="Lister les actualités publiées (les plus récentes d'abord)")
def lister(db: Session = Depends(get_db)):
    return actualite_service.publiees(db)


# The fixed « admin » routes are declared before « /{slug} » so that they are never taken for a slug.
@router.get("/admin", response_model=list[ActualiteOut], summary="Lister toutes les actualités, brouillons compris", responses=NON_AUTORISE)
def lister_admin(db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    return actualite_service.toutes(db)


@router.get(
    "/admin/{actualite_id}",
    response_model=ActualiteOut,
    summary="Voir une actualité, même en brouillon",
    responses={**NON_AUTORISE, **ACTUALITE_INTROUVABLE},
)
def voir_admin(actualite_id: int, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    actualite = actualite_service.par_id(db, actualite_id)
    if actualite is None:
        raise HTTPException(status_code=404, detail="Actualité introuvable")
    return actualite


@router.get("/{slug}", response_model=ActualiteOut, summary="Lire une actualité publiée", responses=ACTUALITE_INTROUVABLE)
def lire(slug: str, db: Session = Depends(get_db)):
    actualite = actualite_service.par_slug_publiee(db, slug)
    if actualite is None:
        raise HTTPException(status_code=404, detail="Actualité introuvable")
    return actualite


@router.post("", response_model=ActualiteOut, status_code=201, summary="Écrire une actualité", responses=NON_AUTORISE)
def creer(payload: ActualiteIn, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    return actualite_service.creer(db, payload.model_dump())


@router.put(
    "/{actualite_id}",
    response_model=ActualiteOut,
    summary="Modifier une actualité (champs envoyés uniquement)",
    responses={**NON_AUTORISE, **ACTUALITE_INTROUVABLE},
)
def modifier(actualite_id: int, payload: ActualiteUpdate, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    actualite = actualite_service.modifier(db, actualite_id, payload.model_dump())
    if actualite is None:
        raise HTTPException(status_code=404, detail="Actualité introuvable")
    return actualite


@router.delete(
    "/{actualite_id}",
    status_code=204,
    summary="Supprimer une actualité et ses photos",
    responses={**NON_AUTORISE, **ACTUALITE_INTROUVABLE},
)
def supprimer(actualite_id: int, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    if not actualite_service.supprimer(db, actualite_id):
        raise HTTPException(status_code=404, detail="Actualité introuvable")
    return Response(status_code=204)


@router.post(
    "/{actualite_id}/photos",
    response_model=PhotoActualiteOut,
    status_code=201,
    summary="Ajouter une photo à une actualité",
    responses={**NON_AUTORISE, **ACTUALITE_INTROUVABLE, 422: {"description": "Ce n'est pas une image acceptée"}},
)
def ajouter_photo(
    actualite_id: int,
    fichier: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    if actualite_service.par_id(db, actualite_id) is None:
        raise HTTPException(status_code=404, detail="Actualité introuvable")
    try:
        url = photo_service.upload_to_cloudinary(fichier)
    except photo_service.ImageInvalideError as erreur:
        raise HTTPException(status_code=422, detail=str(erreur))
    except photo_service.StockageIndisponibleError:
        raise HTTPException(status_code=502, detail=STOCKAGE_INDISPONIBLE)
    return actualite_service.ajouter_photo(db, actualite_id, url)


@router.patch(
    "/photos/{photo_id}",
    response_model=PhotoActualiteOut,
    summary="Modifier la légende d'une photo",
    responses={**NON_AUTORISE, **PHOTO_INTROUVABLE},
)
def legende(photo_id: int, payload: LegendeIn, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    photo = actualite_service.changer_legende(db, photo_id, payload.legende)
    if photo is None:
        raise HTTPException(status_code=404, detail="Photo introuvable")
    return photo


@router.patch(
    "/photos/{photo_id}/couverture",
    response_model=PhotoActualiteOut,
    summary="Choisir une photo comme couverture (affichée en premier)",
    responses={**NON_AUTORISE, **PHOTO_INTROUVABLE},
)
def couverture(photo_id: int, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    photo = actualite_service.choisir_couverture(db, photo_id)
    if photo is None:
        raise HTTPException(status_code=404, detail="Photo introuvable")
    return photo


@router.delete(
    "/photos/{photo_id}",
    status_code=204,
    summary="Supprimer une photo",
    responses={**NON_AUTORISE, **PHOTO_INTROUVABLE},
)
def supprimer_photo(photo_id: int, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    if not actualite_service.supprimer_photo(db, photo_id):
        raise HTTPException(status_code=404, detail="Photo introuvable")
    return Response(status_code=204)
