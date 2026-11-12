from sqlalchemy.orm import Session

from app.models.contenu import ContenuSite

# The texts and photos of the public pages the artisane may change. Anything else is refused.
# Keep in sync with frontend/src/config/contenusSite.js, which holds the original texts and labels.
TEXTE, IMAGE = "texte", "image"
CLES: dict[str, str] = {
    "accueil.titre": TEXTE, "accueil.sous_titre": TEXTE, "accueil.image": IMAGE,
    "accueil.univers_titre": TEXTE, "accueil.univers_texte": TEXTE, "accueil.univers_image": IMAGE,
    "accueil.savoir_faire_titre": TEXTE, "accueil.savoir_faire_texte": TEXTE, "accueil.savoir_faire_image": IMAGE,
    "boutique.meubles_image": IMAGE, "boutique.ceramique_image": IMAGE, "boutique.papeterie_image": IMAGE,
    "actualites.titre": TEXTE, "actualites.intro": TEXTE,
    "apropos.titre": TEXTE, "apropos.introduction": TEXTE, "apropos.bandeau_image": IMAGE,
    "apropos.engagement1_titre": TEXTE, "apropos.engagement1_texte": TEXTE,
    "apropos.engagement2_titre": TEXTE, "apropos.engagement2_texte": TEXTE,
    "apropos.engagement3_titre": TEXTE, "apropos.engagement3_texte": TEXTE,
    "apropos.demarche_titre": TEXTE, "apropos.demarche_texte": TEXTE, "apropos.demarche_image": IMAGE,
    "contact.titre": TEXTE, "contact.introduction": TEXTE, "contact.texte": TEXTE, "contact.image": IMAGE,
}


class CleInconnueError(Exception):
    pass


class MauvaisTypeError(Exception):
    """A text sent for a photo key, or a photo for a text key."""


def _verifier(cle: str, type_attendu: str | None) -> str:
    type_ = CLES.get(cle)
    if type_ is None:
        raise CleInconnueError()
    if type_attendu is not None and type_ != type_attendu:
        raise MauvaisTypeError()
    return type_


def tous(db: Session) -> dict[str, ContenuSite]:
    return {c.cle: c for c in db.query(ContenuSite).all()}


def _ligne(db: Session, cle: str) -> ContenuSite:
    ligne = db.query(ContenuSite).filter(ContenuSite.cle == cle).first()
    if ligne is None:
        ligne = ContenuSite(cle=cle)
        db.add(ligne)
    return ligne


def _nettoyer(db: Session, ligne: ContenuSite) -> None:
    """A row with nothing left in it is deleted: « no row » means « the original »."""
    if not ligne.texte and not ligne.image_url:
        db.delete(ligne)


def definir_texte(db: Session, cle: str, texte: str | None) -> ContenuSite:
    _verifier(cle, TEXTE)
    ligne = _ligne(db, cle)
    ligne.texte = texte or None
    _nettoyer(db, ligne)
    db.commit()
    return ContenuSite(cle=cle, texte=texte or None, image_url=None)


def definir_image(db: Session, cle: str, url: str) -> ContenuSite:
    _verifier(cle, IMAGE)
    ligne = _ligne(db, cle)
    ligne.image_url = url
    db.commit()
    db.refresh(ligne)
    return ligne


def retablir(db: Session, cle: str) -> None:
    _verifier(cle, None)
    db.query(ContenuSite).filter(ContenuSite.cle == cle).delete()
    db.commit()
