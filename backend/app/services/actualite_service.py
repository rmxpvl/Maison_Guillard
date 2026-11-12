import re
import unicodedata

from sqlalchemy.orm import Session

from app.models.actualite import Actualite, PhotoActualite

# Addresses that would hide a route of the API (GET /api/actualites/admin).
RESERVES = {"admin"}


def slugifier(titre: str) -> str:
    """« Été 2026 : l'atelier ouvre ! » -> « ete-2026-l-atelier-ouvre ». Never empty."""
    ascii_ = unicodedata.normalize("NFKD", titre).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_.lower()).strip("-")[:80].strip("-")
    slug = slug or "actualite"
    return f"{slug}-2" if slug in RESERVES else slug


def _slug_libre(db: Session, base: str) -> str:
    candidat, n = base, 2
    while db.query(Actualite.id).filter(Actualite.slug == candidat).first() is not None:
        candidat = f"{base}-{n}"
        n += 1
    return candidat


def publiees(db: Session) -> list[Actualite]:
    return (
        db.query(Actualite).filter(Actualite.publiee.is_(True))
        .order_by(Actualite.date_publication.desc(), Actualite.id.desc()).all()
    )


def toutes(db: Session) -> list[Actualite]:
    return db.query(Actualite).order_by(Actualite.date_publication.desc(), Actualite.id.desc()).all()


def par_slug_publiee(db: Session, slug: str) -> Actualite | None:
    return db.query(Actualite).filter(Actualite.slug == slug, Actualite.publiee.is_(True)).first()


def par_id(db: Session, actualite_id: int) -> Actualite | None:
    return db.query(Actualite).filter(Actualite.id == actualite_id).first()


def creer(db: Session, data: dict) -> Actualite:
    champs = {k: v for k, v in data.items() if v is not None}
    actualite = Actualite(slug=_slug_libre(db, slugifier(data["titre"])), **champs)
    db.add(actualite)
    db.commit()
    db.refresh(actualite)
    return actualite


def modifier(db: Session, actualite_id: int, data: dict) -> Actualite | None:
    actualite = par_id(db, actualite_id)
    if actualite is None:
        return None
    for cle, valeur in data.items():
        if valeur is not None:
            setattr(actualite, cle, valeur)
    db.commit()
    db.refresh(actualite)
    return actualite


def supprimer(db: Session, actualite_id: int) -> bool:
    actualite = par_id(db, actualite_id)
    if actualite is None:
        return False
    db.delete(actualite)
    db.commit()
    return True


def ajouter_photo(db: Session, actualite_id: int, url: str) -> PhotoActualite | None:
    actualite = par_id(db, actualite_id)
    if actualite is None:
        return None
    dernier = max((p.ordre for p in actualite.photos), default=-1)
    photo = PhotoActualite(actualite_id=actualite_id, url=url, ordre=dernier + 1)
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo


def _photo(db: Session, photo_id: int) -> PhotoActualite | None:
    return db.query(PhotoActualite).filter(PhotoActualite.id == photo_id).first()


def changer_legende(db: Session, photo_id: int, legende: str | None) -> PhotoActualite | None:
    photo = _photo(db, photo_id)
    if photo is None:
        return None
    photo.legende = legende or None
    db.commit()
    db.refresh(photo)
    return photo


def choisir_couverture(db: Session, photo_id: int) -> PhotoActualite | None:
    """The cover is the photo with the lowest order: put this one just before all the others."""
    photo = _photo(db, photo_id)
    if photo is None:
        return None
    premier = min(p.ordre for p in par_id(db, photo.actualite_id).photos)
    photo.ordre = premier - 1
    db.commit()
    db.refresh(photo)
    return photo


def supprimer_photo(db: Session, photo_id: int) -> bool:
    photo = _photo(db, photo_id)
    if photo is None:
        return False
    db.delete(photo)
    db.commit()
    return True
