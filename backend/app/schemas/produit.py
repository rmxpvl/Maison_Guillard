from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.photo import PhotoOut
from app.schemas.teinte import TeinteOut


class ProduitCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nom: str = Field(min_length=1, max_length=120)
    description: str
    categorie_id: int
    prix: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    dimensions: str
    visible: bool = True
    teinte_ids: list[int] = []


class ProduitUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nom: Optional[str] = Field(default=None, min_length=1, max_length=120)
    description: Optional[str] = None
    categorie_id: Optional[int] = None
    prix: Optional[Decimal] = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    dimensions: Optional[str] = None
    visible: Optional[bool] = None
    teinte_ids: Optional[list[int]] = None


class ProduitOut(BaseModel):
    id: int
    nom: str
    description: str
    categorie_id: int
    prix: Decimal
    dimensions: str
    visible: bool
    photos: list[PhotoOut] = []
    teintes: list[TeinteOut] = []

    model_config = ConfigDict(from_attributes=True)
