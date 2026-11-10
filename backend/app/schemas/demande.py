from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.demande import StatutDemande


class LigneDemandeIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    produit_id: int
    quantite: int = Field(ge=1, le=10)
    teinte_id: int | None = None
    souhait: str | None = Field(default=None, max_length=500)


class DemandeIn(BaseModel):
    # "   " becomes "" before min_length is checked, so blank fields are refused.
    model_config = ConfigDict(str_strip_whitespace=True)

    nom_client: str = Field(min_length=1, max_length=100)
    email: EmailStr
    telephone: str | None = Field(default=None, max_length=30)
    adresse: str = Field(min_length=1, max_length=300)
    message_client: str | None = Field(default=None, max_length=1000)
    lignes: list[LigneDemandeIn] = Field(min_length=1, max_length=50)

    @field_validator("lignes")
    @classmethod
    def un_produit_par_ligne(cls, lignes: list[LigneDemandeIn]) -> list[LigneDemandeIn]:
        ids = [ligne.produit_id for ligne in lignes]
        if len(ids) != len(set(ids)):
            raise ValueError("Chaque produit ne doit apparaître qu'une fois")
        return lignes


class ProjetLibreIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nom_client: str = Field(min_length=1, max_length=100)
    email: EmailStr
    telephone: str | None = Field(default=None, max_length=30)
    adresse: str | None = Field(default=None, max_length=300)
    produit_id: int | None = None
    description_projet: str = Field(min_length=10, max_length=2000)


class LigneDemandeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    produit_id: int | None
    libelle: str
    quantite: int
    teinte_id: int | None
    teinte_nom: str | None
    souhait: str | None
    prix_indicatif: Decimal | None
    prix_final: Decimal | None


class LigneDevisIn(BaseModel):
    id: int
    prix_final: Decimal = Field(ge=0, max_digits=10, decimal_places=2)


class LigneLibreIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    libelle: str = Field(min_length=1, max_length=200)
    prix: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    quantite: int = Field(ge=1, le=10)


class DevisIn(BaseModel):
    """What the artisane edits: final prices, free lines, delivery fees, message."""

    model_config = ConfigDict(str_strip_whitespace=True)

    lignes: list[LigneDevisIn]
    lignes_libres: list[LigneLibreIn] = Field(default=[], max_length=20)
    frais_livraison: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    message_artisane: str | None = Field(default=None, max_length=2000)


class DemandeOut(BaseModel):
    """Full view, for the back-office and for the customer right after sending."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    jeton: str
    statut: StatutDemande
    nom_client: str
    email: str
    telephone: str | None
    adresse: str | None
    message_client: str | None
    description_projet: str | None
    produit_reference_id: int | None
    frais_livraison: Decimal | None
    message_artisane: str | None
    numero_devis: str | None
    version_devis: int
    devis_envoye_at: datetime | None
    expire_at: datetime | None
    montant_paye: Decimal | None
    payee_at: datetime | None
    date_limite: datetime | None
    rembourse_at: datetime | None
    created_at: datetime
    lignes: list[LigneDemandeOut]
    total_indicatif: Decimal
    total_final: Decimal | None = None
    messages_non_lus: int = 0  # customer messages the artisane has not opened yet
    # Only on the detail route: highest default fee among the univers present.
    frais_livraison_suggere: Decimal | None = None


class DemandePubliqueOut(BaseModel):
    """What the customer sees on the secret quote page: nothing internal, no token."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    statut: StatutDemande
    description_projet: str | None
    message_client: str | None
    frais_livraison: Decimal | None
    message_artisane: str | None
    numero_devis: str | None
    expire_at: datetime | None
    payee_at: datetime | None
    date_limite: datetime | None
    rembourse_at: datetime | None
    created_at: datetime
    lignes: list[LigneDemandeOut]
    total_indicatif: Decimal
    total_final: Decimal | None = None
    atelier_email: str | None = None
    atelier_telephone: str | None = None


class StatutDemandeIn(BaseModel):
    statut: StatutDemande
