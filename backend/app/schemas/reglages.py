from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ReglagesDevis(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, from_attributes=True)

    nom_commercial: str = Field(max_length=100)
    nom_legal: str = Field(max_length=150)
    adresse: str = Field(max_length=300)
    siret: str = Field(max_length=30)
    email: str = Field(max_length=150)
    telephone: str = Field(max_length=30)
    prenom_signature: str = Field(max_length=60)
    mention_tva: str = Field(max_length=300)
    validite_jours: int = Field(ge=1, le=365)
    frais_meubles: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    frais_ceramique: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    frais_papeterie: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    cond_paiement: str = Field(max_length=2000)
    cond_fabrication: str = Field(max_length=2000)
    cond_annulation: str = Field(max_length=2000)


class MessageTypeIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    titre: str = Field(min_length=1, max_length=60)
    texte: str = Field(min_length=1, max_length=2000)


class MessageTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titre: str
    texte: str
    ordre: int
