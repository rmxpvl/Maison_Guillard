from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.services import categorie_service


def test_get_all_returns_categories_from_query():
    db = MagicMock()
    db.query.return_value.all.return_value = ["cat1", "cat2"]

    result = categorie_service.get_all(db)

    assert result == ["cat1", "cat2"]


def test_create_adds_and_commits_a_new_categorie():
    db = MagicMock()

    categorie = categorie_service.create(db, {"nom": "Tables", "slug": "tables"})

    assert categorie.nom == "Tables"
    assert categorie.slug == "tables"
    db.add.assert_called_once()
    db.commit.assert_called_once()


def test_delete_returns_false_when_categorie_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    result = categorie_service.delete(db, 999)

    assert result is False


def test_delete_raises_when_categorie_still_used_by_a_produit():
    db = MagicMock()
    categorie = MagicMock(id=1)
    # first .filter().first() call (fetch the categorie) returns the categorie,
    # second one (check for a referencing produit) returns a produit
    db.query.return_value.filter.return_value.first.side_effect = [categorie, MagicMock()]

    with pytest.raises(categorie_service.CategorieEnUsageError):
        categorie_service.delete(db, 1)


def test_delete_removes_categorie_when_unused():
    db = MagicMock()
    categorie = MagicMock(id=1)
    db.query.return_value.filter.return_value.first.side_effect = [categorie, None]

    result = categorie_service.delete(db, 1)

    assert result is True
    db.delete.assert_called_once_with(categorie)
    db.commit.assert_called_once()

def test_create_raises_and_rolls_back_when_slug_already_exists():
    db = MagicMock()
    db.commit.side_effect = IntegrityError("INSERT ...", {}, Exception("duplicate key"))

    with pytest.raises(categorie_service.SlugDejaUtiliseError):
        categorie_service.create(db, {"nom": "Tables", "slug": "tables"})

    db.rollback.assert_called_once()