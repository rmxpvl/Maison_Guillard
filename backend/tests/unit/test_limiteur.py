import pytest
from fastapi import HTTPException

from app.services import limiteur


def test_laisse_passer_jusqu_au_maximum_puis_refuse_avec_429():
    for _ in range(3):
        limiteur.verifier("test", "1.2.3.4", maximum=3, fenetre=60, maintenant=100.0)

    with pytest.raises(HTTPException) as erreur:
        limiteur.verifier("test", "1.2.3.4", maximum=3, fenetre=60, maintenant=101.0)

    assert erreur.value.status_code == 429
    assert "réessayez" in erreur.value.detail.lower()
    assert 55 <= int(erreur.value.headers["Retry-After"]) <= 60


def test_la_fenetre_glisse_et_libere_les_requetes_anciennes():
    for instant in (100.0, 110.0, 120.0):
        limiteur.verifier("test", "ip", maximum=3, fenetre=60, maintenant=instant)

    with pytest.raises(HTTPException):
        limiteur.verifier("test", "ip", maximum=3, fenetre=60, maintenant=159.0)
    limiteur.verifier("test", "ip", maximum=3, fenetre=60, maintenant=161.0)  # the one of t=100 has expired


def test_chaque_adresse_et_chaque_seau_ont_leur_compteur():
    limiteur.verifier("a", "ip1", maximum=1, fenetre=60, maintenant=1.0)

    limiteur.verifier("a", "ip2", maximum=1, fenetre=60, maintenant=1.0)
    limiteur.verifier("b", "ip1", maximum=1, fenetre=60, maintenant=1.0)
    with pytest.raises(HTTPException):
        limiteur.verifier("a", "ip1", maximum=1, fenetre=60, maintenant=2.0)


def test_une_requete_refusee_ne_prolonge_pas_le_blocage():
    limiteur.verifier("test", "ip", maximum=1, fenetre=60, maintenant=100.0)
    for instant in (110.0, 120.0, 130.0):
        with pytest.raises(HTTPException):
            limiteur.verifier("test", "ip", maximum=1, fenetre=60, maintenant=instant)

    limiteur.verifier("test", "ip", maximum=1, fenetre=60, maintenant=161.0)


def test_reinitialiser_vide_tout():
    limiteur.verifier("test", "ip", maximum=1, fenetre=60, maintenant=1.0)

    limiteur.reinitialiser()

    limiteur.verifier("test", "ip", maximum=1, fenetre=60, maintenant=2.0)


def test_adresse_ip_ignore_x_forwarded_for_sans_proxy_de_confiance(monkeypatch):
    monkeypatch.delenv("TRUST_PROXY", raising=False)
    requete = _requete("10.0.0.1", "6.6.6.6")

    assert limiteur.adresse_ip(requete) == "10.0.0.1"


def test_adresse_ip_prend_la_derniere_entree_derriere_un_proxy_de_confiance(monkeypatch):
    # The proxy appends the real client address at the END: an entry sent by the client sits earlier.
    monkeypatch.setenv("TRUST_PROXY", "1")
    requete = _requete("10.0.0.1", "6.6.6.6, 203.0.113.9")

    assert limiteur.adresse_ip(requete) == "203.0.113.9"


def test_adresse_ip_retombe_sur_la_connexion_sans_en_tete(monkeypatch):
    monkeypatch.setenv("TRUST_PROXY", "1")

    assert limiteur.adresse_ip(_requete("10.0.0.1", None)) == "10.0.0.1"


def _requete(hote, forwarded):
    from types import SimpleNamespace

    en_tetes = {"x-forwarded-for": forwarded} if forwarded else {}
    return SimpleNamespace(client=SimpleNamespace(host=hote), headers=en_tetes)
