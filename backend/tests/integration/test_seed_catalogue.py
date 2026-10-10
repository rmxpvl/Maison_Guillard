import pytest

from app.database import SessionLocal
from app.models.categorie import Categorie
from app.models.produit import Disponibilite, Produit
from seed_catalogue import seed_catalogue


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


def test_seed_catalogue_covers_every_disponibilite(clean_db):
    seed_catalogue(clean_db)

    disponibilites = {p.disponibilite for p in clean_db.query(Produit)}
    assert disponibilites == set(Disponibilite)
