import pytest

from app.database import SessionLocal
from app.models.categorie import Categorie, Univers
from app.models.photo import Photo
from app.models.produit import Produit
from app.models.teinte import Teinte
from seed_catalogue import seed_catalogue, seed_photos, seed_teintes


@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()
    db.query(Produit).delete()
    db.query(Teinte).delete()
    db.query(Categorie).delete()
    db.commit()
    yield db
    db.query(Produit).delete()
    db.query(Teinte).delete()
    db.query(Categorie).delete()
    db.commit()
    db.close()


def test_seed_catalogue_creates_categories_and_produits(clean_db):
    seed_catalogue(clean_db)

    assert clean_db.query(Categorie).count() == 8
    assert clean_db.query(Produit).count() == 20


def test_seed_catalogue_is_idempotent(clean_db):
    seed_catalogue(clean_db)
    seed_catalogue(clean_db)

    assert clean_db.query(Categorie).count() == 8
    assert clean_db.query(Produit).count() == 20


def test_seed_catalogue_tous_les_produits_sont_visibles(clean_db):
    seed_catalogue(clean_db)

    assert clean_db.query(Produit).count() > 0
    assert all(p.visible for p in clean_db.query(Produit))


def test_seed_photos_attaches_photos_in_order_with_first_as_principale(clean_db, tmp_path):
    seed_catalogue(clean_db)
    seed_photos(clean_db, tmp_path)

    produit = clean_db.query(Produit).filter(Produit.nom == "Tabouret Trapèze").one()
    assert [p.ordre for p in produit.photos] == [0, 1, 2]
    assert [p.principale for p in produit.photos] == [True, False, False]
    for photo in produit.photos:
        assert (tmp_path / photo.url.rsplit("/", 1)[1]).is_file()


def test_seed_photos_is_idempotent(clean_db, tmp_path):
    seed_catalogue(clean_db)
    seed_photos(clean_db, tmp_path)
    seed_photos(clean_db, tmp_path)

    assert clean_db.query(Photo).count() == 6


def test_seed_catalogue_couvre_les_trois_univers(clean_db):
    seed_catalogue(clean_db)

    assert {c.univers for c in clean_db.query(Categorie)} == set(Univers)


def test_seed_teintes_cree_cinq_teintes_une_seule_fois(clean_db, tmp_path):
    seed_teintes(clean_db, tmp_path)
    seed_teintes(clean_db, tmp_path)

    assert [t.nom for t in clean_db.query(Teinte).order_by(Teinte.ordre)] == [
        "Naturel", "Charcoal", "Hazelnut", "Bourbon", "Vienna",
    ]
    assert (tmp_path / "teinte-naturel.svg").is_file()


def test_seed_les_meubles_proposent_les_teintes(clean_db, tmp_path):
    seed_catalogue(clean_db)
    seed_teintes(clean_db, tmp_path)

    table = clean_db.query(Produit).filter(Produit.nom == "Table de ferme en chêne").one()
    vase = clean_db.query(Produit).join(Categorie).filter(Categorie.univers == Univers.ceramique).first()
    assert len(table.teintes) == 5
    assert vase.teintes == []
