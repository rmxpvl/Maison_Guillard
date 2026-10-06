from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.require_admin import require_admin
from app.models.produit import Disponibilite
from app.schemas.photo import PhotoOut
from app.schemas.produit import ProduitCreate, ProduitOut, ProduitUpdate
from app.services import photo_service, produit_service

router = APIRouter(prefix="/api/produits", tags=["produits"])


@router.get("", response_model=list[ProduitOut])
def list_produits(
    categorie: int | None = None,
    disponibilite: Disponibilite | None = None,
    db: Session = Depends(get_db),
):
    return produit_service.get_all(db, categorie_id=categorie, disponibilite=disponibilite)


@router.get("/{produit_id}", response_model=ProduitOut)
def get_produit(produit_id: int, db: Session = Depends(get_db)):
    produit = produit_service.get_by_id(db, produit_id)
    if produit is None:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    return produit


@router.post("", response_model=ProduitOut, status_code=201)
def create_produit(
    payload: ProduitCreate,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    try:
        return produit_service.create(db, payload.model_dump())
    except produit_service.CategorieIntrouvableError:
        raise HTTPException(status_code=422, detail="Catégorie introuvable")


@router.put("/{produit_id}", response_model=ProduitOut)
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


@router.delete("/{produit_id}", status_code=204)
def delete_produit(
    produit_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    deleted = produit_service.delete(db, produit_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Produit introuvable")


@router.post("/{produit_id}/photos", response_model=PhotoOut, status_code=201)
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


photos_router = APIRouter(prefix="/api/photos", tags=["photos"])


@photos_router.patch("/{photo_id}/principale", response_model=PhotoOut)
def set_photo_principale(
    photo_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    photo = photo_service.set_principale(db, photo_id)
    if photo is None:
        raise HTTPException(status_code=404, detail="Photo introuvable")
    return photo


@photos_router.delete("/{photo_id}", status_code=204)
def delete_photo(
    photo_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    deleted = photo_service.delete(db, photo_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Photo introuvable")
