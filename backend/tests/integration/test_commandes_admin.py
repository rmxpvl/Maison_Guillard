import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.admin import Admin
from app.models.categorie import Categorie
from app.models.commande import Commande, LigneCommande, StatutCommande
from app.models.produit import Disponibilite, Produit
from app.services import auth_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()
    for modele in (Commande, Produit, Categorie, Admin):
        db.query(modele).delete()
    db.commit()
    yield db
    for modele in (Commande, Produit, Categorie, Admin):
        db.query(modele).delete()
    db.commit()
    db.close()


def _entetes(db):
    db.add(Admin(email="admin@test.com", password_hash=auth_service.hash_password("test-password-123")))
    db.commit()
    return {"Authorization": f"Bearer {auth_service.login(db, 'admin@test.com', 'test-password-123')}"}


def _commande(db, nom_client, statut=StatutCommande.en_attente):
    categorie = db.query(Categorie).first()
    if categorie is None:
        categorie = Categorie(nom="Tables", slug="tables")
        db.add(categorie)
        db.commit()
    produit = Produit(
        nom="Table basse", description="En chêne", categorie_id=categorie.id, prix=199.99,
        dimensions="120x60x40cm", disponibilite=Disponibilite.disponible,
    )
    db.add(produit)
    db.commit()
    commande = Commande(
        nom_client=nom_client, email="client@test.com", adresse="1 rue du Bois", statut=statut,
        lignes=[LigneCommande(produit_id=produit.id, quantite=1, prix_unitaire_snapshot=199.99)],
    )
    db.add(commande)
    db.commit()
    db.refresh(commande)
    return commande


def test_liste_les_commandes_les_plus_recentes_d_abord(clean_db):
    entetes = _entetes(clean_db)
    _commande(clean_db, "Première")
    _commande(clean_db, "Seconde")

    res = client.get("/api/commandes", headers=entetes)

    assert res.status_code == 200
    assert [c["nom_client"] for c in res.json()] == ["Seconde", "Première"]
    assert res.json()[0]["lignes"][0]["nom_produit"] == "Table basse"


def test_filtre_les_commandes_par_statut(clean_db):
    entetes = _entetes(clean_db)
    _commande(clean_db, "En attente")
    _commande(clean_db, "Livrée", statut=StatutCommande.livree)

    res = client.get("/api/commandes?statut=livree", headers=entetes)

    assert [c["nom_client"] for c in res.json()] == ["Livrée"]


def test_change_le_statut_d_une_commande(clean_db):
    entetes = _entetes(clean_db)
    commande = _commande(clean_db, "Jeanne")

    res = client.patch(f"/api/commandes/{commande.id}/statut", json={"statut": "expediee"}, headers=entetes)

    assert res.status_code == 200
    assert res.json()["statut"] == "expediee"


def test_statut_inconnu_refuse(clean_db):
    entetes = _entetes(clean_db)
    commande = _commande(clean_db, "Jeanne")

    res = client.patch(f"/api/commandes/{commande.id}/statut", json={"statut": "perdue"}, headers=entetes)

    assert res.status_code == 422


def test_commande_inconnue_renvoie_404(clean_db):
    res = client.patch("/api/commandes/999999/statut", json={"statut": "livree"}, headers=_entetes(clean_db))

    assert res.status_code == 404
    assert res.json()["detail"] == "Commande introuvable"
