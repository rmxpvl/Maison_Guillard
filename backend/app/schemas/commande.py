from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.commande import StatutCommande


class LigneCommandeIn(BaseModel):
    produit_id: int
    quantite: int = Field(ge=1, le=10)


class CommandeIn(BaseModel):
    # "   " becomes "" before min_length is checked, so blank fields are refused.
    model_config = ConfigDict(str_strip_whitespace=True)

    nom_client: str = Field(min_length=1, max_length=100)
    email: EmailStr
    telephone: str | None = Field(default=None, max_length=30)
    adresse: str = Field(min_length=1, max_length=300)
    lignes: list[LigneCommandeIn] = Field(min_length=1, max_length=50)

    @field_validator("lignes")
    @classmethod
    def un_produit_par_ligne(cls, lignes: list[LigneCommandeIn]) -> list[LigneCommandeIn]:
        ids = [ligne.produit_id for ligne in lignes]
        if len(ids) != len(set(ids)):
            raise ValueError("Chaque produit ne doit apparaître qu'une fois")
        return lignes


class LigneCommandeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    produit_id: int
    quantite: int
    prix_unitaire_snapshot: Decimal
    nom_produit: str | None = None


class CommandeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom_client: str
    email: str
    telephone: str | None
    adresse: str
    statut: StatutCommande
    created_at: datetime
    lignes: list[LigneCommandeOut]
    total: Decimal


class StatutCommandeIn(BaseModel):
    statut: StatutCommande