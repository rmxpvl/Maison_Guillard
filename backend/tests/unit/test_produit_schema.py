import pytest
from pydantic import ValidationError

from app.schemas.produit import ProduitCreate, ProduitUpdate

VALIDE = {
    "nom": "Table",
    "description": "Chêne",
    "categorie_id": 1,
    "prix": "120.00",
    "dimensions": "80x80",
    "disponibilite": "disponible",
}


@pytest.mark.parametrize(
    "champ, valeur", [("prix", "0"), ("prix", "-5"), ("nom", ""), ("nom", "   ")]
)
def test_produit_create_refuse(champ, valeur):
    with pytest.raises(ValidationError):
        ProduitCreate(**{**VALIDE, champ: valeur})


def test_produit_update_refuse_un_prix_negatif():
    with pytest.raises(ValidationError):
        ProduitUpdate(prix="-1")


def test_produit_create_retire_les_espaces_du_nom():
    assert ProduitCreate(**{**VALIDE, "nom": "  Table  "}).nom == "Table"
