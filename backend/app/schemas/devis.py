from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.devis import StatutDevis


class DevisIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nom_client: str = Field(min_length=1, max_length=100)
    email: EmailStr
    telephone: str | None = Field(default=None, max_length=30)
    produit_id: int | None = None
    description_projet: str = Field(min_length=10, max_length=2000)


class DevisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom_client: str
    email: str
    telephone: str | None
    produit_id: int | None
    description_projet: str
    statut: StatutDevis
    created_at: datetime
