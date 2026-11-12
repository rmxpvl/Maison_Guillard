import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# Toutes les routes réservées à l'admin : (méthode HTTP, URL).
# Les ids n'ont pas besoin d'exister : la protection est vérifiée avant tout le reste.
ROUTES_ADMIN = [
    ("post", "/api/categories"),
    ("put", "/api/categories/1"),
    ("delete", "/api/categories/1"),
    ("get", "/api/produits/admin"),
    ("get", "/api/produits/admin/1"),
    ("post", "/api/produits"),
    ("put", "/api/produits/1"),
    ("delete", "/api/produits/1"),
    ("post", "/api/produits/1/photos"),
    ("patch", "/api/photos/1/principale"),
    ("delete", "/api/photos/1"),
    ("get", "/api/teintes"),
    ("post", "/api/teintes"),
    ("put", "/api/teintes/1"),
    ("post", "/api/teintes/1/image"),
    ("delete", "/api/teintes/1"),
    ("get", "/api/demandes"),
    ("get", "/api/demandes/1"),
    ("patch", "/api/demandes/1/statut"),
    ("post", "/api/demandes/1/devis"),
    ("post", "/api/demandes/1/devis/apercu"),
    ("get", "/api/demandes/1/devis.pdf"),
    ("post", "/api/demandes/1/rembourser"),
    ("get", "/api/demandes/1/messages"),
    ("post", "/api/demandes/1/messages"),
    ("get", "/api/actualites/admin"),
    ("get", "/api/actualites/admin/1"),
    ("post", "/api/actualites"),
    ("put", "/api/actualites/1"),
    ("delete", "/api/actualites/1"),
    ("post", "/api/actualites/1/photos"),
    ("patch", "/api/actualites/photos/1"),
    ("patch", "/api/actualites/photos/1/couverture"),
    ("delete", "/api/actualites/photos/1"),
    ("put", "/api/contenus/accueil.titre"),
    ("post", "/api/contenus/boutique.ceramique_image/image"),
    ("delete", "/api/contenus/accueil.titre"),
    ("get", "/api/reglages-devis"),
    ("put", "/api/reglages-devis"),
    ("get", "/api/messages-types"),
    ("post", "/api/messages-types"),
    ("put", "/api/messages-types/1"),
    ("delete", "/api/messages-types/1"),
]


@pytest.mark.parametrize("methode, url", ROUTES_ADMIN)
def test_admin_route_rejects_request_without_token(methode, url):
    res = client.request(methode, url)

    assert res.status_code == 401


@pytest.mark.parametrize("methode, url", ROUTES_ADMIN)
def test_admin_route_rejects_forged_token(methode, url):
    res = client.request(methode, url, headers={"Authorization": "Bearer jeton-invente"})

    assert res.status_code == 401
