from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.models.produit import Disponibilite
from app.services import commande_service


def _produit(id, prix, disponibilite=Disponibilite.disponible, nom="Table basse"):
    return MagicMock(id=id, prix=Decimal(prix), disponibilite=disponibilite, nom=nom)


def _data(lignes):
    return {
        "nom_client": "Jeanne Martin",
        "email": "jeanne@test.com",
        "telephone": None,
        "adresse": "1 rue du Bois",
        "lignes": lignes,
    }


def _db_qui_trouve(*produits):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.side_effect = list(produits)
    return db


def test_create_prend_le_prix_en_base_et_calcule_le_total():
    db = _db_qui_trouve(_produit(1, "199.99"), _produit(2, "50.00"))

    commande = commande_service.create(
        db,
        _data([
            # An extra "prix" key from a malicious client must be ignored.
            {"produit_id": 1, "quantite": 2, "prix": "0.01"},
            {"produit_id": 2, "quantite": 1},
        ]),
    )

    assert [l.prix_unitaire_snapshot for l in commande.lignes] == [Decimal("199.99"), Decimal("50.00")]
    assert commande.total == Decimal("449.98")
    db.add.assert_called_once()
    db.commit.assert_called_once()


@pytest.mark.parametrize("disponibilite", [Disponibilite.rupture, Disponibilite.sur_commande])
def test_create_refuse_un_produit_non_disponible(disponibilite):
    db = _db_qui_trouve(_produit(3, "80.00", disponibilite, nom="Lampe"))

    with pytest.raises(commande_service.ProduitIndisponibleError) as erreur:
        commande_service.create(db, _data([{"produit_id": 3, "quantite": 1}]))

    assert erreur.value.nom == "Lampe"
    db.commit.assert_not_called()


def test_create_refuse_un_produit_inconnu():
    db = _db_qui_trouve(None)

    with pytest.raises(commande_service.ProduitIntrouvableError) as erreur:
        commande_service.create(db, _data([{"produit_id": 999, "quantite": 1}]))

    assert erreur.value.produit_id == 999
    db.commit.assert_not_called()
