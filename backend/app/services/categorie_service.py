from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.categorie import Categorie
from app.models.produit import Produit


class CategorieEnUsageError(Exception):
    """Raised when deleting a category still referenced by at least one produit."""

class SlugDejaUtiliseError(Exception):
    """Raised when creating a category whose slug already exists."""

def get_all(db: Session) -> list[Categorie]:
    return db.query(Categorie).all()


def create(db: Session, data: dict) -> Categorie:
    categorie = Categorie(**data)
    db.add(categorie)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise SlugDejaUtiliseError()
    db.refresh(categorie)
    return categorie


def delete(db: Session, categorie_id: int) -> bool:
    categorie = db.query(Categorie).filter(Categorie.id == categorie_id).first()
    if categorie is None:
        return False

    in_use = (
        db.query(Produit).filter(Produit.categorie_id == categorie_id).first()
        is not None
    )
    if in_use:
        raise CategorieEnUsageError()

    db.delete(categorie)
    db.commit()
    return True
