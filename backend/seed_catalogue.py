import shutil
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.orm import Session

load_dotenv()

from app.database import SessionLocal
from app.models.categorie import Categorie
from app.models.photo import Photo
from app.models.produit import Disponibilite, Produit
from app.services import photo_service

SEED_PHOTOS_DIR = Path(__file__).resolve().parent / "seed_photos"

CATEGORIES = [
    ("Tables", "tables"),
    ("Chaises", "chaises"),
    ("Tabourets", "tabourets"),
    ("Lampes", "lampes"),
]

# (slug catégorie, nom, description, prix, dimensions, disponibilité)
PRODUITS = [
    ("tables", "Table de ferme en chêne",
     "Plateau massif en chêne brut, pieds tournés à la main, finition huile naturelle.",
     "890.00", "200x90x76cm", Disponibilite.disponible),
    ("tables", "Table basse en noyer",
     "Pièce unique en noyer massif, assemblages à tenons et mortaises.",
     "420.00", "110x60x40cm", Disponibilite.rupture),
    ("tables", "Table en frêne sur mesure",
     "Fabriquée à la demande : essence, dimensions et finition à définir ensemble.",
     "1200.00", "Dimensions au choix", Disponibilite.sur_commande),
    ("chaises", "Chaise paillée",
     "Structure en hêtre, assise paillée à la main.",
     "180.00", "45x48x88cm", Disponibilite.disponible),
    ("chaises", "Chaise en hêtre cintré",
     "Dossier cintré à la vapeur, fabriquée à la demande.",
     "240.00", "44x50x85cm", Disponibilite.sur_commande),
    ("chaises", "Fauteuil en chêne et lin",
     "Assise garnie de lin naturel, accoudoirs en chêne.",
     "560.00", "62x70x80cm", Disponibilite.rupture),
    ("tabourets", "Tabouret Trapèze",
     "Assise en frêne massif abouté, fendue en deux planches, posée sur deux pieds "
     "évasés reliés par une traverse.",
     "145.00", "38x30x46cm", Disponibilite.disponible),
    ("tabourets", "Tabouret Croisé",
     "Assise ronde en chêne massif sur un piètement de deux cadres triangulaires croisés.",
     "190.00", "Ø35x46cm", Disponibilite.disponible),
    ("tabourets", "Banc Trapèze",
     "Banc en frêne massif assorti au Tabouret Trapèze, pieds obliques. "
     "Longueur adaptable à la demande.",
     "320.00", "120x30x45cm", Disponibilite.sur_commande),
    ("lampes", "Lampe de chevet en bois flotté",
     "Pied en bois flotté du Léman, abat-jour en lin.",
     "85.00", "20x20x40cm", Disponibilite.disponible),
    ("lampes", "Lampadaire en noyer",
     "Fût en noyer tourné, fabriqué à la demande.",
     "320.00", "40x40x160cm", Disponibilite.sur_commande),
    ("lampes", "Suspension en hêtre tourné",
     "Abat-jour tourné dans un bloc de hêtre.",
     "140.00", "35x35x30cm", Disponibilite.rupture),
]

# nom du produit -> fichiers de seed_photos/, dans l'ordre ; le premier est la principale
PHOTOS = {
    "Tabouret Trapèze": [
        "tabouret-trapeze-1.webp",
        "tabouret-trapeze-2.webp",
        "tabouret-trapeze-3.webp",
    ],
    "Tabouret Croisé": ["tabouret-croise-1.webp", "tabouret-croise-2.webp"],
    "Banc Trapèze": ["banc-trapeze-1.webp"],
}


def seed_catalogue(db: Session) -> None:
    categories = {}
    for nom, slug in CATEGORIES:
        categorie = db.query(Categorie).filter(Categorie.slug == slug).first()
        if categorie is None:
            categorie = Categorie(nom=nom, slug=slug)
            db.add(categorie)
            db.flush()  # assigns categorie.id before the produits need it
        categories[slug] = categorie

    for slug, nom, description, prix, dimensions, disponibilite in PRODUITS:
        if db.query(Produit).filter(Produit.nom == nom).first() is None:
            db.add(
                Produit(
                    nom=nom,
                    description=description,
                    categorie_id=categories[slug].id,
                    prix=Decimal(prix),
                    dimensions=dimensions,
                    disponibilite=disponibilite,
                )
            )
    db.commit()


def seed_photos(db: Session, upload_dir: Path) -> None:
    """Copies the demo photos into upload_dir and attaches them to their produit.
    A produit that already has photos is left untouched, so the admin's own
    photos are never mixed with the demo ones."""
    upload_dir.mkdir(parents=True, exist_ok=True)
    for nom, fichiers in PHOTOS.items():
        produit = db.query(Produit).filter(Produit.nom == nom).first()
        if produit is None or produit.photos:
            continue
        for ordre, fichier in enumerate(fichiers):
            shutil.copyfile(SEED_PHOTOS_DIR / fichier, upload_dir / fichier)
            db.add(
                Photo(
                    produit_id=produit.id,
                    url=photo_service.public_url(fichier),
                    ordre=ordre,
                    principale=(ordre == 0),
                )
            )
    db.commit()


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_catalogue(db)
        seed_photos(db, photo_service.UPLOAD_DIR)
        print("Catalogue de démonstration en place.")
    finally:
        db.close()