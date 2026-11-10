from decimal import Decimal
from types import SimpleNamespace

from app.services import reglages_service


def _reglages(**extra):
    base = dict(
        nom_legal="EI Camille Guillard", adresse="3 rue de l'Atelier, 69000 Lyon",
        siret="123 456 789 00012", email="atelier@test.com",
        frais_meubles=Decimal("60"), frais_ceramique=Decimal("15"), frais_papeterie=Decimal("5"),
    )
    base.update(extra)
    return SimpleNamespace(**base)


def test_aucun_champ_obligatoire_manquant():
    assert reglages_service.champs_manquants(_reglages()) == []


def test_champs_obligatoires_manquants_dans_l_ordre():
    r = _reglages(nom_legal="", adresse="  ", siret="", email="")
    assert reglages_service.champs_manquants(r) == ["nom légal", "adresse", "SIRET", "e-mail"]


def test_frais_par_defaut_prend_le_plus_eleve_des_univers_presents():
    r = _reglages()
    assert reglages_service.frais_par_defaut(["ceramique", "papeterie"], r) == Decimal("15")
    assert reglages_service.frais_par_defaut(["meubles", "ceramique"], r) == Decimal("60")
    assert reglages_service.frais_par_defaut(["papeterie"], r) == Decimal("5")


def test_frais_par_defaut_sans_univers_vaut_zero():
    assert reglages_service.frais_par_defaut([], _reglages()) == Decimal("0")
