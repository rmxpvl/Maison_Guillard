from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.teinte import Teinte


class TeinteUtiliseeError(Exception):
    """Raised when deleting a teinte that at least one produit offers."""


class TeinteIntrouvableError(Exception):
    """Raised when a produit references a teinte id that does not exist."""


def get_all(db: Session) -> list[Teinte]:
    return db.query(Teinte).order_by(Teinte.ordre, Teinte.id).all()


def get_many(db: Session, ids: list[int]) -> list[Teinte]:
    wanted = set(ids)
    teintes = db.query(Teinte).filter(Teinte.id.in_(wanted)).all()
    if len({t.id for t in teintes}) != len(wanted):
        raise TeinteIntrouvableError()
    return teintes


def create(db: Session, nom: str, ordre: int, image_url: str) -> Teinte:
    teinte = Teinte(nom=nom, ordre=ordre, image_url=image_url)
    db.add(teinte)
    db.commit()
    db.refresh(teinte)
    return teinte


def update(db: Session, teinte_id: int, data: dict) -> Teinte | None:
    teinte = db.query(Teinte).filter(Teinte.id == teinte_id).first()
    if teinte is None:
        return None
    for key, value in data.items():
        if value is not None:
            setattr(teinte, key, value)
    db.commit()
    db.refresh(teinte)
    return teinte


def replace_image(db: Session, teinte_id: int, image_url: str) -> Teinte | None:
    return update(db, teinte_id, {"image_url": image_url})


def delete(db: Session, teinte_id: int) -> bool:
    teinte = db.query(Teinte).filter(Teinte.id == teinte_id).first()
    if teinte is None:
        return False
    db.delete(teinte)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise TeinteUtiliseeError()
    return True
