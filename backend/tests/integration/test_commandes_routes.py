import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.categorie import Categorie
from app.models.commande import Commande
from app.models.parametre import Parametre
from app.models.produit import Disponibilite, Produit

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()
    # Commande first: its lines reference produits.
    for modele in (Commande, Parametre, Produit, Categorie):
        db.query(modele).delete()
    db.commit()
    yield db
    for modele in (Commande, Parametre, Produit, Categorie):
        db.query(modele).delete()
    db.commit()
    db.close()


def _produit(db, nom="Table basse", prix=199.99, disponibilite=Disponibilite.disponible):
    categorie = db.query(Categorie).first()
    if categorie is None:
        categorie = Categorie(nom="Tables", slug="tables")
        db.add(categorie)
        db.commit()
    produit = Produit(
        nom=nom, description="En chêne", categorie_id=categorie.id, prix=prix,
        dimensions="120x60x40cm", disponibilite=disponibilite,
    )
    db.add(produit)
    db.commit()
    db.refresh(produit)
    return produit


def _corps(lignes):
    return {
        "nom_client": "Jeanne Martin",
        "email": "jeanne@test.com",
        "telephone": "06 12 34 56 78",
        "adresse": "1 rue du Bois, 44000 Nantes",
        "lignes": lignes,
    }


def test_post_commande_cree_la_commande_en_attente(clean_db):
    table = _produit(clean_db, prix=199.99)
    lampe = _produit(clean_db, nom="Lampe", prix=80)

    res = client.post("/api/commandes", json=_corps([
        {"produit_id": table.id, "quantite": 2},
        {"produit_id": lampe.id, "quantite": 1},
    ]))

    assert res.status_code == 201
    body = res.json()
    assert body["statut"] == "en_attente"
    assert body["total"] == "479.98"
    assert [l["prix_unitaire_snapshot"] for l in body["lignes"]] == ["199.99", "80.00"]
    assert clean_db.query(Commande).count() == 1


@pytest.mark.parametrize("disponibilite", [Disponibilite.rupture, Disponibilite.sur_commande])
def test_post_commande_refuse_un_produit_non_disponible(clean_db, disponibilite):
    produit = _produit(clean_db, nom="Tabouret", disponibilite=disponibilite)

    res = client.post("/api/commandes", json=_corps([{"produit_id": produit.id, "quantite": 1}]))

    assert res.status_code == 422
    assert res.json()["detail"] == "« Tabouret » n'est plus disponible"
    assert clean_db.query(Commande).count() == 0


def test_post_commande_refuse_un_produit_inconnu(clean_db):
    res = client.post("/api/commandes", json=_corps([{"produit_id": 999999, "quantite": 1}]))

    assert res.status_code == 422
    assert res.json()["detail"] == "Produit n°999999 introuvable"


def test_post_commande_refuse_un_corps_invalide(clean_db):
    res = client.post("/api/commandes", json=_corps([]))

    assert res.status_code == 422
    assert isinstance(res.json()["detail"], list)  # Pydantic's validation format
