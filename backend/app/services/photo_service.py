
import hashlib
import os
import time
import uuid
from pathlib import Path
from urllib.parse import urlparse

import httpx
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.photo import Photo

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"


def public_url(filename: str) -> str:
    """URL under which a file stored in UPLOAD_DIR is served by the StaticFiles mount."""
    port = os.environ.get("PORT", "3000")
    return f"http://localhost:{port}/uploads/{filename}"


class ImageInvalideError(Exception):
    """The uploaded file is not an acceptable image (message in French, shown to the artisane)."""


class StockageIndisponibleError(Exception):
    """The image storage (Cloudinary) is unreachable or refused the image."""


# SVG is left out on purpose: an SVG can carry scripts.
EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
TAILLE_MAX = 8 * 1024 * 1024
DOSSIER_CLOUDINARY = "maison-guillard"


def _lire_et_verifier(fichier: UploadFile) -> tuple[bytes, str]:
    ext = Path(fichier.filename or "").suffix.lower()
    type_contenu = fichier.content_type
    if ext not in EXTENSIONS or (type_contenu and not type_contenu.startswith("image/")):
        raise ImageInvalideError("Format non accepté : envoyez une image JPG, PNG, WebP ou GIF.")
    contenu = fichier.file.read(TAILLE_MAX + 1)
    if len(contenu) > TAILLE_MAX:
        raise ImageInvalideError("Image trop lourde : 8 Mo au plus.")
    if not contenu:
        raise ImageInvalideError("Le fichier est vide.")
    return contenu, ext


def _config_cloudinary() -> tuple[str, str, str] | None:
    """(cloud name, api key, api secret) from CLOUDINARY_URL=cloudinary://KEY:SECRET@CLOUD."""
    adresse = os.environ.get("CLOUDINARY_URL")
    if not adresse:
        return None
    analyse = urlparse(adresse)
    if analyse.scheme != "cloudinary" or not (analyse.hostname and analyse.username and analyse.password):
        raise StockageIndisponibleError("CLOUDINARY_URL mal formée")
    return analyse.hostname, analyse.username, analyse.password


def _envoyer_cloudinary(contenu: bytes, ext: str, config: tuple[str, str, str]) -> str:
    cloud, cle, secret = config
    horodatage = int(time.time())
    # Signed upload: the signature covers the parameters, the secret never leaves the server.
    a_signer = f"folder={DOSSIER_CLOUDINARY}&timestamp={horodatage}"
    signature = hashlib.sha1(f"{a_signer}{secret}".encode()).hexdigest()
    try:
        reponse = httpx.post(
            f"https://api.cloudinary.com/v1_1/{cloud}/image/upload",
            data={"api_key": cle, "timestamp": horodatage, "folder": DOSSIER_CLOUDINARY, "signature": signature},
            files={"file": (f"image{ext}", contenu)},
            timeout=30,
        )
        if reponse.status_code != 200:
            raise StockageIndisponibleError(f"Cloudinary a répondu {reponse.status_code}")
        return reponse.json()["secure_url"]
    except (httpx.HTTPError, KeyError, ValueError) as erreur:
        raise StockageIndisponibleError(str(erreur)) from erreur


def _enregistrer_local(contenu: bytes, ext: str) -> str:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    # The stored name is random: the name sent by the browser is never used.
    nom = f"{uuid.uuid4().hex}{ext}"
    (UPLOAD_DIR / nom).write_bytes(contenu)
    return public_url(nom)


def upload_to_cloudinary(fichier: UploadFile) -> str:
    """Checks the image, then stores it on Cloudinary when CLOUDINARY_URL is set (production: the
    disk of the host is erased at each deploy) or in uploads/ otherwise (local development).
    Returns its URL. Used for product photos and finish images alike."""
    contenu, ext = _lire_et_verifier(fichier)
    config = _config_cloudinary()
    if config is not None:
        return _envoyer_cloudinary(contenu, ext, config)
    return _enregistrer_local(contenu, ext)


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
