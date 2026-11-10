import re
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image

from app.services.photo_service import UPLOAD_DIR

_FILL = re.compile(r"""fill\s*=\s*["'](#[0-9a-fA-F]{6})["']""")


def couleur_depuis_url(url: str) -> str | None:
    """Colour (#rrggbb) of a teinte's image, for the swatch printed on the quote PDF.

    Works on files stored in uploads/ (an SVG's fill, or the average colour of a picture); an
    image hosted elsewhere, a missing or unreadable file gives None and the quote simply shows
    the finish name without a swatch."""
    chemin = urlparse(url).path
    if not chemin.startswith("/uploads/"):
        return None
    nom = chemin[len("/uploads/"):]
    if "/" in nom or "\\" in nom or nom.startswith("."):
        return None  # never leave the uploads folder
    fichier: Path = UPLOAD_DIR / nom
    try:
        if not fichier.is_file():
            return None
        if fichier.suffix.lower() == ".svg":
            trouve = _FILL.search(fichier.read_text(encoding="utf-8"))
            return trouve.group(1).lower() if trouve else None
        with Image.open(fichier) as image:
            r, g, b = image.convert("RGB").resize((1, 1), Image.Resampling.BOX).getpixel((0, 0))
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return None
