import pytest

from app.services import actualite_service


@pytest.mark.parametrize("titre, attendu", [
    ("Nouvelle collection d'automne", "nouvelle-collection-d-automne"),
    ("  Été 2026 : l'atelier ouvre ses portes !  ", "ete-2026-l-atelier-ouvre-ses-portes"),
    ("Céramique & papeterie", "ceramique-papeterie"),
    ("---", "actualite"),
    ("   ", "actualite"),
    ("日本語", "actualite"),
])
def test_slugifier_donne_une_adresse_lisible_sans_accent(titre, attendu):
    assert actualite_service.slugifier(titre) == attendu


def test_slugifier_borne_la_longueur():
    assert len(actualite_service.slugifier("mot " * 100)) <= 80


def test_le_mot_admin_est_reserve_pour_ne_pas_cacher_la_route_d_administration():
    assert actualite_service.slugifier("Admin") != "admin"
