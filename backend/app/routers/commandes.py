from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.commande import CommandeIn, CommandeOut
from app.services import commande_service

router = APIRouter(prefix="/api/commandes", tags=["Commandes"])


@router.post(
    "",
    response_model=CommandeOut,
    status_code=201,
    summary="Passer une commande",
    responses={422: {"description": "Données invalides, produit introuvable ou indisponible"}},
)
def create_commande(payload: CommandeIn, db: Session = Depends(get_db)):
    try:
        commande = commande_service.create(db, payload.model_dump())
    except commande_service.ProduitIntrouvableError as erreur:
        raise HTTPException(status_code=422, detail=f"Produit n°{erreur.produit_id} introuvable")
    except commande_service.ProduitIndisponibleError as erreur:
        raise HTTPException(status_code=422, detail=f"« {erreur.nom} » n'est plus disponible")
    return commande
