from sqlalchemy.orm import Session

from app.models.devis import Devis, StatutDevis
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


def get_all(db: Session, statut: StatutDevis | None = None) -> list[Devis]:
    query = db.query(Devis)
    if statut is not None:
        query = query.filter(Devis.statut == statut)
    return query.order_by(Devis.created_at.desc(), Devis.id.desc()).all()


def update_statut(db: Session, devis_id: int, statut: StatutDevis) -> Devis | None:
    devis = db.query(Devis).filter(Devis.id == devis_id).first()
    if devis is None:
        return None
    devis.statut = statut
    db.commit()
    db.refresh(devis)
    return devis
