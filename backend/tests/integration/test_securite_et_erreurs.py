import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# Toutes les routes réservées à l'admin : (méthode HTTP, URL).
# Les ids n'ont pas besoin d'exister : la protection est vérifiée avant tout le reste.
ROUTES_ADMIN = [
    ("post", "/api/categories"),
    ("delete", "/api/categories/1"),
    ("post", "/api/produits"),
    ("put", "/api/produits/1"),
    ("delete", "/api/produits/1"),
    ("post", "/api/produits/1/photos"),
    ("patch", "/api/photos/1/principale"),
    ("delete", "/api/photos/1"),
    ("get", "/api/parametres"),
    ("put", "/api/parametres"),
    ("get", "/api/commandes"),
    ("patch", "/api/commandes/1/statut"),
    ("get", "/api/devis"),
    ("patch", "/api/devis/1/statut"),
]


@pytest.mark.parametrize("methode, url", ROUTES_ADMIN)
def test_admin_route_rejects_request_without_token(methode, url):
    res = client.request(methode, url)

    assert res.status_code == 401


@pytest.mark.parametrize("methode, url", ROUTES_ADMIN)
def test_admin_route_rejects_forged_token(methode, url):
    res = client.request(methode, url, headers={"Authorization": "Bearer jeton-invente"})

    assert res.status_code == 401
