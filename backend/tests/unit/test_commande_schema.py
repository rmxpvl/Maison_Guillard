import pytest
from pydantic import ValidationError

from app.schemas.commande import CommandeIn


def _commande(**changes):
    data = {
        "nom_client": "Jeanne Martin",
        "email": "jeanne@test.com",
        "adresse": "1 rue du Bois, 44000 Nantes",
        "lignes": [{"produit_id": 1, "quantite": 2}],
    }
    data.update(changes)
    return data


def test_commande_valide_sans_telephone():
    commande = CommandeIn(**_commande())
    assert commande.telephone is None


@pytest.mark.parametrize(
    "changes",
    [
        {"lignes": []},
        {"lignes": [{"produit_id": 1, "quantite": 0}]},
        {"lignes": [{"produit_id": 1, "quantite": 11}]},
        {"lignes": [{"produit_id": 1, "quantite": 1}, {"produit_id": 1, "quantite": 2}]},
        {"email": "pas-un-email"},
        {"nom_client": "   "},
        {"adresse": ""},
    ],
)
def test_commande_invalide_est_refusee(changes):
    with pytest.raises(ValidationError):
        CommandeIn(**_commande(**changes))
