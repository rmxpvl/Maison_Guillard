from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.produit import Produit


class CategorieIntrouvableError(Exception):
    """Raised when a produit references a categorie_id that does not exist."""


def _commit_or_raise_categorie_introuvable(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise CategorieIntrouvableError()


def get_all(
    db: Session, categorie_id: int | None = None, disponibilite: str | None = None
) -> list[Produit]:
    query = db.query(Produit)
    if categorie_id is not None:
        query = query.filter(Produit.categorie_id == categorie_id)
    if disponibilite is not None:
        query = query.filter(Produit.disponibilite == disponibilite)
    return query.all()


def get_by_id(db: Session, produit_id: int) -> Produit | None:
    return db.query(Produit).filter(Produit.id == produit_id).first()


def create(db: Session, data: dict) -> Produit:
    produit = Produit(**data)
    db.add(produit)
    _commit_or_raise_categorie_introuvable(db)
    db.refresh(produit)
    return produit


def update(db: Session, produit_id: int, data: dict) -> Produit | None:
    produit = get_by_id(db, produit_id)
    if produit is None:
        return None

    for key, value in data.items():
        if value is not None:
            setattr(produit, key, value)

    _commit_or_raise_categorie_introuvable(db)
    db.refresh(produit)
    return produit


def delete(db: Session, produit_id: int) -> bool:
    produit = get_by_id(db, produit_id)
    if produit is None:
        return False

    db.delete(produit)
    db.commit()
    return True
