import pytest
from pydantic import ValidationError

from app.schemas.demande import DemandeIn, ProjetLibreIn

CLIENT = {"nom_client": "Jeanne Martin", "email": "jeanne@test.com", "adresse": "1 rue du Bois"}
LIGNE = {"produit_id": 1, "quantite": 2}


def test_demande_valide_avec_teinte_et_souhait():
    d = DemandeIn(**CLIENT, lignes=[{**LIGNE, "teinte_id": 3, "souhait": " plus haute "}])

    assert d.lignes[0].teinte_id == 3
    assert d.lignes[0].souhait == "plus haute"
    assert d.telephone is None and d.message_client is None


@pytest.mark.parametrize("quantite", [0, 11, -1])
def test_demande_refuse_une_quantite_hors_limites(quantite):
    with pytest.raises(ValidationError):
        DemandeIn(**CLIENT, lignes=[{**LIGNE, "quantite": quantite}])


def test_demande_refuse_un_souhait_trop_long():
    with pytest.raises(ValidationError):
        DemandeIn(**CLIENT, lignes=[{**LIGNE, "souhait": "x" * 501}])


def test_demande_refuse_zero_ligne_et_doublons():
    with pytest.raises(ValidationError):
        DemandeIn(**CLIENT, lignes=[])
    with pytest.raises(ValidationError):
        DemandeIn(**CLIENT, lignes=[LIGNE, LIGNE])


@pytest.mark.parametrize("champ, valeur", [("nom_client", "   "), ("email", "pas-un-mail"), ("adresse", "")])
def test_demande_refuse_des_coordonnees_invalides(champ, valeur):
    with pytest.raises(ValidationError):
        DemandeIn(**{**CLIENT, champ: valeur}, lignes=[LIGNE])


def test_projet_libre_n_exige_ni_adresse_ni_produit():
    p = ProjetLibreIn(nom_client="Jeanne", email="jeanne@test.com", description_projet="Une grande table en frêne")

    assert p.adresse is None and p.produit_id is None


def test_projet_libre_refuse_une_description_trop_courte():
    with pytest.raises(ValidationError):
        ProjetLibreIn(nom_client="Jeanne", email="jeanne@test.com", description_projet="court")
