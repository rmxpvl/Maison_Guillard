from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.services import teinte_service


def test_delete_refuse_une_teinte_utilisee():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = MagicMock(id=1)
    db.commit.side_effect = IntegrityError("DELETE ...", {}, Exception("fk"))

    with pytest.raises(teinte_service.TeinteUtiliseeError):
        teinte_service.delete(db, 1)

    db.rollback.assert_called_once()


def test_get_many_leve_si_un_id_manque():
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = [MagicMock(id=1)]

    with pytest.raises(teinte_service.TeinteIntrouvableError):
        teinte_service.get_many(db, [1, 2])


def test_update_change_les_champs_envoyes():
    db = MagicMock()
    teinte = MagicMock(nom="Naturel", ordre=0, active=True)
    db.query.return_value.filter.return_value.first.return_value = teinte

    result = teinte_service.update(db, 1, {"nom": None, "ordre": 3, "active": False})

    assert result.nom == "Naturel"
    assert result.ordre == 3
    assert result.active is False
    db.commit.assert_called_once()
