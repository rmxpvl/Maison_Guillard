from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.demande import StatutDemande
from app.models.message_demande import AuteurMessage


def _adresse(valeur: str) -> str:
    return valeur.strip().lower()


def _mot_de_passe(valeur: str) -> str:
    # bcrypt reads 72 bytes only: refuse a longer password instead of silently cutting it.
    if len(valeur.encode("utf-8")) > 72:
        raise ValueError("Le mot de passe est trop long (72 caractères au plus)")
    return valeur


class InscriptionIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr

    _normaliser = field_validator("email", mode="after")(_adresse)


class MotDePasseOublieIn(InscriptionIn):
    pass


class ConnexionIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr
    mot_de_passe: str = Field(min_length=1, max_length=200)

    _normaliser = field_validator("email", mode="after")(_adresse)


class ActivationIn(BaseModel):
    token: str = Field(min_length=1, max_length=200)
    mot_de_passe: str = Field(min_length=8, max_length=200)

    _borne = field_validator("mot_de_passe", mode="after")(_mot_de_passe)


class ReinitialisationIn(ActivationIn):
    pass


class SupprimerCompteIn(BaseModel):
    mot_de_passe: str = Field(min_length=1, max_length=200)


class TokenOut(BaseModel):
    token: str


class MessageGenerique(BaseModel):
    message: str


class DemandeCompteOut(BaseModel):
    """One line of « Mes demandes »: enough to show it and open it (its link carries the thread)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    jeton: str
    statut: StatutDemande
    numero_affiche: str | None
    created_at: datetime
    libelles: list[str]
    total_indicatif: Decimal
    total_final: Decimal | None
    messages_non_lus: int = 0


class MoiOut(BaseModel):
    email: str
    demandes: list[DemandeCompteOut]


class MessageIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    texte: str = Field(min_length=1, max_length=2000)


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    auteur: AuteurMessage
    texte: str
    created_at: datetime
