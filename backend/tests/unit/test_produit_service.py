from unittest.mock import MagicMock
import pytest
from sqlalchemy.exc import IntegrityError

from app.services import produit_service
from app.models.produit import Disponibilite


def test_create_adds_and_commits_a_new_produit():
    db = MagicMock()

    produit = produit_service.create(
        db,
        {
            "nom": "Table basse",
            "description": "En chêne",
            "categorie_id": 1,
            "prix": 199.99,
            "dimensions": "120x60x40cm",
            "disponibilite": Disponibilite.disponible,
        },
    )

    assert produit.nom == "Table basse"
    db.add.assert_called_once()
    db.commit.assert_called_once()


def test_get_by_id_returns_none_when_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    result = produit_service.get_by_id(db, 999)

    assert result is None


def test_update_returns_none_when_produit_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    result = produit_service.update(db, 999, {"nom": "Nouveau nom"})

    assert result is None


def test_update_only_overwrites_fields_present_in_data():
    db = MagicMock()
    existing = MagicMock(nom="Ancien nom", prix=100)
    db.query.return_value.filter.return_value.first.return_value = existing

    produit_service.update(db, 1, {"nom": "Nouveau nom", "prix": None})

    assert existing.nom == "Nouveau nom"
    assert existing.prix == 100  # untouched: None means "not provided"
    db.commit.assert_called_once()


def test_delete_returns_false_when_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    result = produit_service.delete(db, 999)

    assert result is False


def test_delete_returns_true_and_removes_when_found():
    db = MagicMock()
    produit = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = produit

    result = produit_service.delete(db, 1)

    assert result is True
    db.delete.assert_called_once_with(produit)
    db.commit.assert_called_once()


def test_create_raises_and_rolls_back_when_categorie_does_not_exist():
    db = MagicMock()
    db.commit.side_effect = IntegrityError("INSERT ...", {}, Exception("foreign key"))

    with pytest.raises(produit_service.CategorieIntrouvableError):
        produit_service.create(
            db,
            {
                "nom": "Table basse",
                "description": "En chêne",
                "categorie_id": 999,
                "prix": 199.99,
                "dimensions": "120x60x40cm",
                "disponibilite": Disponibilite.disponible,
            },
        )

    db.rollback.assert_called_once()


def test_update_raises_and_rolls_back_when_categorie_does_not_exist():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = MagicMock()
    db.commit.side_effect = IntegrityError("UPDATE ...", {}, Exception("foreign key"))

    with pytest.raises(produit_service.CategorieIntrouvableError):
        produit_service.update(db, 1, {"categorie_id": 999})

    db.rollback.assert_called_once()
