from sqlalchemy.orm import Session

from app.models.devis import Devis
from app.models.produit import Produit
from app.services.commande_service import ProduitIntrouvableError


def create(db: Session, data: dict) -> Devis:
    # Any disponibilité is fine for a quote: only an unknown produit is refused.
    produit_id = data.get("produit_id")
    if produit_id is not None:
        if db.query(Produit).filter(Produit.id == produit_id).first() is None:
            raise ProduitIntrouvableError(produit_id)

    devis = Devis(**data)
    db.add(devis)
    db.commit()
    db.refresh(devis)
    return devis
