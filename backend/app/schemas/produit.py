from decimal import Decimal
from typing import Optional

from pydantic import BaseModel

from app.models.produit import Disponibilite
from app.schemas.photo import PhotoOut


class ProduitCreate(BaseModel):
    nom: str
    description: str
    categorie_id: int
    prix: Decimal
    dimensions: str
    disponibilite: Disponibilite


class ProduitUpdate(BaseModel):
    nom: Optional[str] = None
    description: Optional[str] = None
    categorie_id: Optional[int] = None
    prix: Optional[Decimal] = None
    dimensions: Optional[str] = None
    disponibilite: Optional[Disponibilite] = None


class ProduitOut(BaseModel):
    id: int
    nom: str
    description: str
    categorie_id: int
    prix: Decimal
    dimensions: str
    disponibilite: Disponibilite
    photos: list[PhotoOut] = []

    class Config:
        from_attributes = True
