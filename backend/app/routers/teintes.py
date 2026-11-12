from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.require_admin import require_admin
from app.routers.reponses import NON_AUTORISE, TEINTE_INTROUVABLE
from app.schemas.teinte import TeinteOut, TeinteUpdate
from app.services import photo_service, teinte_service

router = APIRouter(prefix="/api/teintes", tags=["Teintes"])


@router.get("", response_model=list[TeinteOut], summary="Lister les teintes", responses=NON_AUTORISE)
def list_teintes(db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    return teinte_service.get_all(db)


@router.post(
    "",
    response_model=TeinteOut,
    status_code=201,
    summary="Créer une teinte avec son image",
    responses=NON_AUTORISE,
)
def create_teinte(
    nom: str = Form(..., min_length=1, max_length=40),
    ordre: int = Form(0, ge=0),
    fichier: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    url = photo_service.upload_to_cloudinary(fichier)
    return teinte_service.create(db, nom.strip(), ordre, url)


@router.put(
    "/{teinte_id}",
    response_model=TeinteOut,
    summary="Modifier une teinte (champs envoyés uniquement)",
    responses={**NON_AUTORISE, **TEINTE_INTROUVABLE},
)
def update_teinte(
    teinte_id: int,
    payload: TeinteUpdate,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    teinte = teinte_service.update(db, teinte_id, payload.model_dump())
    if teinte is None:
        raise HTTPException(status_code=404, detail="Teinte introuvable")
    return teinte


@router.post(
    "/{teinte_id}/image",
    response_model=TeinteOut,
    summary="Remplacer l'image d'une teinte",
    responses={**NON_AUTORISE, **TEINTE_INTROUVABLE},
)
def replace_image(
    teinte_id: int,
    fichier: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    url = photo_service.upload_to_cloudinary(fichier)
    teinte = teinte_service.replace_image(db, teinte_id, url)
    if teinte is None:
        raise HTTPException(status_code=404, detail="Teinte introuvable")
    return teinte


@router.delete(
    "/{teinte_id}",
    status_code=204,
    summary="Supprimer une teinte",
    responses={
        **NON_AUTORISE,
        **TEINTE_INTROUVABLE,
        409: {"description": "Teinte proposée par des produits"},
    },
)
def delete_teinte(
    teinte_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    try:
        deleted = teinte_service.delete(db, teinte_id)
    except teinte_service.TeinteUtiliseeError:
        raise HTTPException(
            status_code=409, detail="Teinte proposée par des produits : désactivez-la"
        )
    if not deleted:
        raise HTTPException(status_code=404, detail="Teinte introuvable")
