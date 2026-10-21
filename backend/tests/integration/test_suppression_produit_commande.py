import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.admin import Admin
from app.models.categorie import Categorie
from app.models.commande import Commande, LigneCommande
from app.models.produit import Disponibilite, Produit
from app.services import auth_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()
    # Commande first: its lines reference produits.
    for modele in (Commande, Produit, Categorie, Admin):
        db.query(modele).delete()
    db.commit()
    yield db
    for modele in (Commande, Produit, Categorie, Admin):
        db.query(modele).delete()
    db.commit()
    db.close()


def _admin_token(db):
    db.add(Admin(email="admin@test.com", password_hash=auth_service.hash_password("test-password-123")))
    db.commit()
    return auth_service.login(db, "admin@test.com", "test-password-123")


def test_delete_produit_present_dans_une_commande_renvoie_409(clean_db):
    token = _admin_token(clean_db)
    categorie = Categorie(nom="Tables", slug="tables")
    clean_db.add(categorie)
    clean_db.commit()
    produit = Produit(
        nom="Table basse", description="En chêne", categorie_id=categorie.id,
        prix=199.99, dimensions="120x60x40cm", disponibilite=Disponibilite.disponible,
    )
    clean_db.add(produit)
    clean_db.commit()
    clean_db.add(Commande(
        nom_client="Jeanne", email="jeanne@test.com", adresse="1 rue du Bois",
        lignes=[LigneCommande(produit_id=produit.id, quantite=1, prix_unitaire_snapshot=199.99)],
    ))
    clean_db.commit()

    res = client.delete(f"/api/produits/{produit.id}", headers={"Authorization": f"Bearer {token}"})

    assert res.status_code == 409
    assert "rupture" in res.json()["detail"]
