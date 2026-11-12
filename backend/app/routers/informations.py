from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import paiement_service, reglages_service

router = APIRouter(prefix="/api/informations-legales", tags=["Informations légales"])


class InformationsLegales(BaseModel):
    nom_commercial: str
    nom_legal: str
    adresse: str
    siret: str
    email: str
    telephone: str
    mention_tva: str
    cgv_version: str


@router.get(
    "",
    response_model=InformationsLegales,
    summary="Identité de l'entreprise et version des CGV, pour les pages légales",
)
def informations_legales(db: Session = Depends(get_db)):
    """Public on purpose: it is what the legal notice prints. Only identity fields, nothing else of the settings."""
    r = reglages_service.get(db)
    return InformationsLegales(
        nom_commercial=r.nom_commercial, nom_legal=r.nom_legal, adresse=r.adresse, siret=r.siret,
        email=r.email, telephone=r.telephone, mention_tva=r.mention_tva,
        cgv_version=paiement_service.CGV_VERSION,
    )
