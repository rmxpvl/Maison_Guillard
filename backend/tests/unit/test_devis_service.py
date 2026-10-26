from unittest.mock import MagicMock

import pytest

from app.models.produit import Disponibilite
from app.services import commande_service, devis_service


def _data(produit_id=None):
    return {
        "nom_client": "Jeanne Martin",
        "email": "jeanne@test.com",
        "telephone": None,
        "produit_id": produit_id,
        "description_projet": "Une table en chêne de 2 mètres.",
    }


def test_create_enregistre_une_demande_sans_produit():
    db = MagicMock()

    devis = devis_service.create(db, _data())

    assert devis.nom_client == "Jeanne Martin"
    assert devis.produit_id is None
    db.query.assert_not_called()  # nothing to check without a produit
    db.add.assert_called_once()
    db.commit.assert_called_once()


def test_create_refuse_un_produit_inconnu():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(commande_service.ProduitIntrouvableError) as erreur:
        devis_service.create(db, _data(produit_id=999))

    assert erreur.value.produit_id == 999
    db.commit.assert_not_called()


@pytest.mark.parametrize("disponibilite", [Disponibilite.rupture, Disponibilite.sur_commande])
def test_create_accepte_un_produit_quelle_que_soit_sa_disponibilite(disponibilite):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = MagicMock(
        id=3, disponibilite=disponibilite
    )

    devis = devis_service.create(db, _data(produit_id=3))

    assert devis.produit_id == 3
    db.commit.assert_called_once()
