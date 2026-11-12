from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from app.models.demande import StatutDemande
from app.services import demande_service

S = StatutDemande


@pytest.mark.parametrize(
    "depart, arrivee",
    [
        (S.nouvelle, S.annulee), (S.devis_envoye, S.annulee), (S.payee, S.en_fabrication),
        (S.en_fabrication, S.expediee), (S.expediee, S.livree),
    ],
)
def test_transitions_admin_autorisees(depart, arrivee):
    assert demande_service.transition_autorisee(depart, arrivee)


@pytest.mark.parametrize(
    "depart, arrivee",
    [
        (S.nouvelle, S.livree), (S.nouvelle, S.payee), (S.livree, S.annulee), (S.annulee, S.nouvelle),
        (S.payee, S.livree), (S.expediee, S.en_fabrication), (S.refusee, S.annulee),
    ],
)
def test_transitions_admin_refusees(depart, arrivee):
    assert not demande_service.transition_autorisee(depart, arrivee)


def test_expiration_paresseuse_marque_un_devis_depasse_comme_expire():
    db = MagicMock()
    demande = MagicMock(statut=S.devis_envoye, expire_at=datetime.now(timezone.utc) - timedelta(days=1))

    demande_service.appliquer_expiration(db, demande)

    assert demande.statut == S.expiree
    db.commit.assert_called_once()


def test_expiration_paresseuse_laisse_un_devis_valide():
    db = MagicMock()
    demande = MagicMock(statut=S.devis_envoye, expire_at=datetime.now(timezone.utc) + timedelta(days=5))

    demande_service.appliquer_expiration(db, demande)

    assert demande.statut == S.devis_envoye
    db.commit.assert_not_called()


def test_expiration_paresseuse_ignore_les_autres_statuts():
    db = MagicMock()
    demande = MagicMock(statut=S.payee, expire_at=datetime.now(timezone.utc) - timedelta(days=1))

    demande_service.appliquer_expiration(db, demande)

    assert demande.statut == S.payee
