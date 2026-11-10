import pytest
from pydantic import ValidationError

from app.schemas.client import ActivationIn, ConnexionIn, InscriptionIn, MessageIn, ReinitialisationIn


def test_inscription_normalise_l_adresse():
    assert InscriptionIn(email="  Jeanne.Martin@Test.COM ").email == "jeanne.martin@test.com"
    assert ConnexionIn(email="JEANNE@test.com", mot_de_passe="x").email == "jeanne@test.com"


def test_inscription_refuse_une_adresse_invalide():
    with pytest.raises(ValidationError):
        InscriptionIn(email="pas-un-mail")


@pytest.mark.parametrize("modele", [ActivationIn, ReinitialisationIn])
def test_mot_de_passe_trop_court_refuse(modele):
    with pytest.raises(ValidationError):
        modele(token="t", mot_de_passe="court")


@pytest.mark.parametrize("modele", [ActivationIn, ReinitialisationIn])
def test_mot_de_passe_au_dela_de_72_octets_refuse(modele):
    # bcrypt only reads 72 bytes: a longer password would be silently cut.
    with pytest.raises(ValidationError):
        modele(token="t", mot_de_passe="é" * 40)  # 80 bytes
    assert modele(token="t", mot_de_passe="é" * 36).mot_de_passe == "é" * 36  # 72 bytes


def test_message_refuse_vide_ou_trop_long():
    assert MessageIn(texte="  Bonjour  ").texte == "Bonjour"
    for texte in ("", "   ", "x" * 2001):
        with pytest.raises(ValidationError):
            MessageIn(texte=texte)
