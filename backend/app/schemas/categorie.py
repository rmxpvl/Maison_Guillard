from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.categorie import Univers


class CategorieCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nom: str = Field(min_length=1, max_length=60)
    slug: str = Field(pattern=r"^[a-z0-9-]+$", max_length=60)
    univers: Univers


class CategorieUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nom: Optional[str] = Field(default=None, min_length=1, max_length=60)
    slug: Optional[str] = Field(default=None, pattern=r"^[a-z0-9-]+$", max_length=60)
    univers: Optional[Univers] = None


class CategorieOut(BaseModel):
    id: int
    nom: str
    slug: str
    univers: Univers

    model_config = ConfigDict(from_attributes=True)
