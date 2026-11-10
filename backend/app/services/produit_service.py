from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.categorie import Categorie, Univers
from app.models.produit import Produit


class CategorieIntrouvableError(Exception):
    """Raised when a produit references a categorie_id that does not exist."""


class ProduitEnCommandeError(Exception):
    """Raised when deleting a produit that appears in at least one order line."""


def _commit_or_raise_categorie_introuvable(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise CategorieIntrouvableError()


def get_all(
    db: Session,
    categorie_id: int | None = None,
    univers: Univers | None = None,
    visibles_seulement: bool = True,
) -> list[Produit]:
    query = db.query(Produit)
    if visibles_seulement:
        query = query.filter(Produit.visible.is_(True))
    if univers is not None:
        query = query.join(Categorie, Produit.categorie_id == Categorie.id).filter(
            Categorie.univers == univers
        )
    if categorie_id is not None:
        query = query.filter(Produit.categorie_id == categorie_id)
    return query.all()


def get_by_id(db: Session, produit_id: int) -> Produit | None:
    return db.query(Produit).filter(Produit.id == produit_id).first()


def get_visible(db: Session, produit_id: int) -> Produit | None:
    return (
        db.query(Produit)
        .filter(Produit.id == produit_id, Produit.visible.is_(True))
        .first()
    )


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
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ProduitEnCommandeError()
    return True
