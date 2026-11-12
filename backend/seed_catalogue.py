import shutil
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.orm import Session

load_dotenv()

from app.database import SessionLocal
from app.models.categorie import Categorie, Univers
from app.models.photo import Photo
from app.models.produit import Produit
from app.models.teinte import Teinte
from app.services import photo_service

SEED_PHOTOS_DIR = Path(__file__).resolve().parent / "seed_photos"

CATEGORIES = [
    ("Tables", "tables", Univers.meubles),
    ("Chaises", "chaises", Univers.meubles),
    ("Tabourets", "tabourets", Univers.meubles),
    ("Lampes", "lampes", Univers.meubles),
    ("Vases", "vases", Univers.ceramique),
    ("Bols et tasses", "bols-et-tasses", Univers.ceramique),
    ("Carnets", "carnets", Univers.papeterie),
    ("Cartes", "cartes", Univers.papeterie),
]

# (slug catégorie, nom, description, prix, dimensions)
PRODUITS = [
    ("tables", "Table de ferme en chêne",
     "Plateau massif en chêne brut, pieds tournés à la main, finition huile naturelle.",
     "890.00", "200x90x76cm"),
    ("tables", "Table basse en noyer",
     "Pièce unique en noyer massif, assemblages à tenons et mortaises.",
     "420.00", "110x60x40cm"),
    ("tables", "Table en frêne sur mesure",
     "Fabriquée à la demande : essence, dimensions et finition à définir ensemble.",
     "1200.00", "Dimensions au choix"),
    ("chaises", "Chaise paillée",
     "Structure en hêtre, assise paillée à la main.",
     "180.00", "45x48x88cm"),
    ("chaises", "Chaise en hêtre cintré",
     "Dossier cintré à la vapeur, fabriquée à la demande.",
     "240.00", "44x50x85cm"),
    ("chaises", "Fauteuil en chêne et lin",
     "Assise garnie de lin naturel, accoudoirs en chêne.",
     "560.00", "62x70x80cm"),
    ("tabourets", "Tabouret Trapèze",
     "Assise en frêne massif abouté, fendue en deux planches, posée sur deux pieds "
     "évasés reliés par une traverse.",
     "145.00", "38x30x46cm"),
    ("tabourets", "Tabouret Croisé",
     "Assise ronde en chêne massif sur un piètement de deux cadres triangulaires croisés.",
     "190.00", "Ø35x46cm"),
    ("tabourets", "Banc Trapèze",
     "Banc en frêne massif assorti au Tabouret Trapèze, pieds obliques. "
     "Longueur adaptable à la demande.",
     "320.00", "120x30x45cm"),
    ("lampes", "Lampe de chevet en bois flotté",
     "Pied en bois flotté du Léman, abat-jour en lin.",
     "85.00", "20x20x40cm"),
    ("lampes", "Lampadaire en noyer",
     "Fût en noyer tourné, fabriqué à la demande.",
     "320.00", "40x40x160cm"),
    ("lampes", "Suspension en hêtre tourné",
     "Abat-jour tourné dans un bloc de hêtre.",
     "140.00", "35x35x30cm"),
    ("vases", "Vase soliflore grès",
     "Vase tourné en grès, émail mat, une pièce unique à chaque cuisson.",
     "48.00", "Ø9x22cm"),
    ("vases", "Grand vase ovale",
     "Grand vase aux courbes douces, émail satiné crème.",
     "96.00", "24x16x38cm"),
    ("bols-et-tasses", "Bol à déjeuner",
     "Bol tourné main, émail intérieur lisse, passe au lave-vaisselle.",
     "28.00", "Ø14x7cm"),
    ("bols-et-tasses", "Tasse sans anse",
     "Tasse tournée main, tenue ronde et chaude, 25 cl.",
     "24.00", "Ø8x8cm"),
    ("carnets", "Carnet cousu main",
     "Couverture en papier texturé, 96 pages ivoire, reliure japonaise.",
     "16.00", "A5"),
    ("carnets", "Carnet de croquis",
     "Papier épais 120 g, dos toilé, s'ouvre bien à plat.",
     "19.00", "A4"),
    ("cartes", "Lot de six cartes illustrées",
     "Six cartes dessinées à la main, imprimées sur papier recyclé, enveloppes fournies.",
     "12.00", "10x15cm"),
    ("cartes", "Carte de vœux gravée",
     "Gravure sur bois imprimée à la main, tirage limité.",
     "6.00", "12x17cm"),
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
    for nom, slug, univers in CATEGORIES:
        categorie = db.query(Categorie).filter(Categorie.slug == slug).first()
        if categorie is None:
            categorie = Categorie(nom=nom, slug=slug, univers=univers)
            db.add(categorie)
            db.flush()  # assigns categorie.id before the produits need it
        categories[slug] = categorie

    for slug, nom, description, prix, dimensions in PRODUITS:
        if db.query(Produit).filter(Produit.nom == nom).first() is None:
            db.add(
                Produit(
                    nom=nom,
                    description=description,
                    categorie_id=categories[slug].id,
                    prix=Decimal(prix),
                    dimensions=dimensions,
                )
            )
    db.commit()


# (nom, fichier de seed_photos/teintes/) dans l'ordre d'affichage
TEINTES = [
    ("Naturel", "naturel.svg"),
    ("Charcoal", "charcoal.svg"),
    ("Hazelnut", "hazelnut.svg"),
    ("Bourbon", "bourbon.svg"),
    ("Vienna", "vienna.svg"),
]


def seed_teintes(db: Session, upload_dir: Path) -> None:
    """Creates the demo teintes (once, by nom) and offers all of them on every
    meuble that has none yet. Safe to run before or after seed_catalogue."""
    upload_dir.mkdir(parents=True, exist_ok=True)
    for ordre, (nom, fichier) in enumerate(TEINTES):
        if db.query(Teinte).filter(Teinte.nom == nom).first() is None:
            nom_public = f"teinte-{fichier}"
            shutil.copyfile(SEED_PHOTOS_DIR / "teintes" / fichier, upload_dir / nom_public)
            db.add(
                Teinte(nom=nom, ordre=ordre, image_url=photo_service.public_url(nom_public))
            )
    db.flush()

    teintes = db.query(Teinte).order_by(Teinte.ordre).all()
    meubles = (
        db.query(Produit)
        .join(Categorie, Produit.categorie_id == Categorie.id)
        .filter(Categorie.univers == Univers.meubles)
        .all()
    )
    for produit in meubles:
        if not produit.teintes:
            produit.teintes = teintes
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
        seed_teintes(db, photo_service.UPLOAD_DIR)
        seed_photos(db, photo_service.UPLOAD_DIR)
        print("Catalogue de démonstration en place.")
    finally:
        db.close()