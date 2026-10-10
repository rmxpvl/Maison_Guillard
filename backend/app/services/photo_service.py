
import os
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.photo import Photo

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"


def public_url(filename: str) -> str:
    """URL under which a file stored in UPLOAD_DIR is served by the StaticFiles mount."""
    port = os.environ.get("PORT", "3000")
    return f"http://localhost:{port}/uploads/{filename}"


def upload_to_cloudinary(fichier: UploadFile) -> str:
    """Stub: saves the file locally instead of calling the real Cloudinary API.
    Keeps the same shape (takes a file, returns a URL) a real integration would
    have, so swapping this out later touches only this function."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(fichier.filename).suffix
    unique_name = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_DIR / unique_name

    with dest.open("wb") as out:
        out.write(fichier.file.read())

    return public_url(unique_name)


def attach_to_produit(db: Session, produit_id: int, url: str, ordre: int = 0) -> Photo:
    photo = Photo(produit_id=produit_id, url=url, ordre=ordre, principale=False)
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo


def delete(db: Session, photo_id: int) -> bool:
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if photo is None:
        return False

    db.delete(photo)
    db.commit()
    return True


def set_principale(db: Session, photo_id: int) -> Photo | None:
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if photo is None:
        return None

    db.query(Photo).filter(Photo.produit_id == photo.produit_id).update(
        {"principale": False}, synchronize_session=False
    )
    photo.principale = True
    db.commit()
    db.refresh(photo)
    return photo
