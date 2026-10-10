from decimal import Decimal

from dotenv import load_dotenv
from sqlalchemy.orm import Session

load_dotenv()

from app.database import SessionLocal
from app.models.categorie import Categorie
from app.models.produit import Disponibilite, Produit

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
    ("tabourets", "Tabouret de bar en orme",
     "Assise creusée dans un plateau d'orme, repose-pieds en chêne.",
     "150.00", "35x35x75cm", Disponibilite.disponible),
    ("tabourets", "Tabouret tripode",
     "Trois pieds en frêne, assise ronde en chêne.",
     "95.00", "30x30x45cm", Disponibilite.disponible),
    ("tabourets", "Banc-tabouret en chêne",
     "Banc d'appoint en chêne massif, longueur à la demande.",
     "210.00", "90x30x45cm", Disponibilite.sur_commande),
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


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_catalogue(db)
        print("Catalogue de démonstration en place.")
    finally:
        db.close()