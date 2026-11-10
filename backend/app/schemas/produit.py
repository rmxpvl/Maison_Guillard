from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.produit import Disponibilite
from app.schemas.photo import PhotoOut


class ProduitCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nom: str = Field(min_length=1, max_length=120)
    description: str
    categorie_id: int
    prix: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    dimensions: str
    disponibilite: Disponibilite


class ProduitUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nom: Optional[str] = Field(default=None, min_length=1, max_length=120)
    description: Optional[str] = None
    categorie_id: Optional[int] = None
    prix: Optional[Decimal] = Field(default=None, gt=0, max_digits=10, decimal_places=2)
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

    model_config = ConfigDict(from_attributes=True)
