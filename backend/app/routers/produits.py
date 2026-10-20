from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.require_admin import require_admin
from app.models.produit import Disponibilite
from app.routers.reponses import NON_AUTORISE, PHOTO_INTROUVABLE, PRODUIT_INTROUVABLE
from app.schemas.photo import PhotoOut
from app.schemas.produit import ProduitCreate, ProduitOut, ProduitUpdate
from app.services import photo_service, produit_service

router = APIRouter(prefix="/api/produits", tags=["Produits"])


@router.get("", response_model=list[ProduitOut], summary="Lister les produits")
def list_produits(
    categorie: int | None = None,
    disponibilite: Disponibilite | None = None,
    db: Session = Depends(get_db),
):
    return produit_service.get_all(db, categorie_id=categorie, disponibilite=disponibilite)


@router.get(
    "/{produit_id}",
    response_model=ProduitOut,
    summary="Voir un produit",
    responses=PRODUIT_INTROUVABLE,
)
def get_produit(produit_id: int, db: Session = Depends(get_db)):
    produit = produit_service.get_by_id(db, produit_id)
    if produit is None:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    return produit


@router.post(
    "",
    response_model=ProduitOut,
    status_code=201,
    summary="Créer un produit",
    responses={**NON_AUTORISE, 422: {"description": "Données invalides ou catégorie introuvable"}},
)
def create_produit(
    payload: ProduitCreate,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    try:
        return produit_service.create(db, payload.model_dump())
    except produit_service.CategorieIntrouvableError:
        raise HTTPException(status_code=422, detail="Catégorie introuvable")


@router.put(
    "/{produit_id}",
    response_model=ProduitOut,
    summary="Modifier un produit (champs envoyés uniquement)",
    responses={**NON_AUTORISE, **PRODUIT_INTROUVABLE, 422: {"description": "Données invalides ou catégorie introuvable"}},
)
def update_produit(
    produit_id: int,
    payload: ProduitUpdate,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    try:
        produit = produit_service.update(db, produit_id, payload.model_dump())
    except produit_service.CategorieIntrouvableError:
        raise HTTPException(status_code=422, detail="Catégorie introuvable")
    if produit is None:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    return produit


@router.delete(
    "/{produit_id}",
    status_code=204,
    summary="Supprimer un produit et ses photos",
    responses={**NON_AUTORISE, **PRODUIT_INTROUVABLE},
)
def delete_produit(
    produit_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    deleted = produit_service.delete(db, produit_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Produit introuvable")


@router.post(
    "/{produit_id}/photos",
    response_model=PhotoOut,
    status_code=201,
    summary="Ajouter une photo à un produit",
    responses={**NON_AUTORISE, **PRODUIT_INTROUVABLE},
)
def add_photo(
    produit_id: int,
    fichier: UploadFile = File(...),
    ordre: int = Form(0),
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    produit = produit_service.get_by_id(db, produit_id)
    if produit is None:
        raise HTTPException(status_code=404, detail="Produit introuvable")

    url = photo_service.upload_to_cloudinary(fichier)
    return photo_service.attach_to_produit(db, produit_id, url, ordre)


photos_router = APIRouter(prefix="/api/photos", tags=["Photos"])


@photos_router.patch(
    "/{photo_id}/principale",
    response_model=PhotoOut,
    summary="Définir la photo principale",
    responses={**NON_AUTORISE, **PHOTO_INTROUVABLE},
)
def set_photo_principale(
    photo_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    photo = photo_service.set_principale(db, photo_id)
    if photo is None:
        raise HTTPException(status_code=404, detail="Photo introuvable")
    return photo


@photos_router.delete(
    "/{photo_id}",
    status_code=204,
    summary="Supprimer une photo",
    responses={**NON_AUTORISE, **PHOTO_INTROUVABLE},
)
def delete_photo(
    photo_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    deleted = photo_service.delete(db, photo_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Photo introuvable")
