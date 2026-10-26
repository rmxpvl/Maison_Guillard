import pytest
from pydantic import ValidationError

from app.schemas.devis import DevisIn


def _demande(**changes):
    data = {
        "nom_client": "Jeanne Martin",
        "email": "jeanne@test.com",
        "description_projet": "Une table en chêne de 2 mètres pour 8 personnes.",
    }
    data.update(changes)
    return data


def test_demande_valide_sans_telephone_ni_produit():
    devis = DevisIn(**_demande())
    assert devis.telephone is None
    assert devis.produit_id is None


@pytest.mark.parametrize(
    "changes",
    [
        {"description_projet": "court"},
        {"description_projet": "            "},
        {"email": "pas-un-email"},
        {"nom_client": "   "},
    ],
)
def test_demande_invalide_est_refusee(changes):
    with pytest.raises(ValidationError):
        DevisIn(**_demande(**changes))
