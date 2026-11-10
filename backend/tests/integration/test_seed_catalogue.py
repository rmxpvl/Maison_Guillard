import pytest

from app.database import SessionLocal
from app.models.categorie import Categorie
from app.models.photo import Photo
from app.models.produit import Produit
from seed_catalogue import seed_catalogue, seed_photos


@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()
    db.query(Produit).delete()
    db.query(Categorie).delete()
    db.commit()
    yield db
    db.query(Produit).delete()
    db.query(Categorie).delete()
    db.commit()
    db.close()


def test_seed_catalogue_creates_categories_and_produits(clean_db):
    seed_catalogue(clean_db)

    assert clean_db.query(Categorie).count() == 4
    assert clean_db.query(Produit).count() == 12


def test_seed_catalogue_is_idempotent(clean_db):
    seed_catalogue(clean_db)
    seed_catalogue(clean_db)

    assert clean_db.query(Categorie).count() == 4
    assert clean_db.query(Produit).count() == 12


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
