from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.require_admin import require_admin
from app.schemas.categorie import CategorieCreate, CategorieOut
from app.services import categorie_service

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=list[CategorieOut])
def list_categories(db: Session = Depends(get_db)):
    return categorie_service.get_all(db)


@router.post("", response_model=CategorieOut, status_code=201)
def create_categorie(
    payload: CategorieCreate,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    try:
        return categorie_service.create(db, payload.model_dump())
    except categorie_service.SlugDejaUtiliseError:
        raise HTTPException(status_code=409, detail="Slug déjà utilisé")


@router.delete("/{categorie_id}", status_code=204)
def delete_categorie(
    categorie_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    try:
        deleted = categorie_service.delete(db, categorie_id)
    except categorie_service.CategorieEnUsageError:
        raise HTTPException(status_code=409, detail="Catégorie utilisée par des produits")
    if not deleted:
        raise HTTPException(status_code=404, detail="Catégorie introuvable")