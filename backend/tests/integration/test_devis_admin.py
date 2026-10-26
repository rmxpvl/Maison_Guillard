import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.admin import Admin
from app.models.categorie import Categorie
from app.models.devis import Devis, StatutDevis
from app.models.produit import Disponibilite, Produit
from app.services import auth_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()
    for modele in (Devis, Produit, Categorie, Admin):
        db.query(modele).delete()
    db.commit()
    yield db
    for modele in (Devis, Produit, Categorie, Admin):
        db.query(modele).delete()
    db.commit()
    db.close()


def _entetes(db):
    db.add(Admin(email="admin@test.com", password_hash=auth_service.hash_password("test-password-123")))
    db.commit()
    return {"Authorization": f"Bearer {auth_service.login(db, 'admin@test.com', 'test-password-123')}"}


def _produit(db):
    categorie = Categorie(nom="Tables", slug="tables")
    db.add(categorie)
    db.commit()
    produit = Produit(
        nom="Table en frêne", description="Sur mesure", categorie_id=categorie.id, prix=1200,
        dimensions="200x90x75cm", disponibilite=Disponibilite.sur_commande,
    )
    db.add(produit)
    db.commit()
    return produit


def _devis(db, nom_client, produit_id=None, statut=StatutDevis.nouveau):
    devis = Devis(
        nom_client=nom_client, email="client@test.com", produit_id=produit_id,
        description_projet="Une table de 2 mètres pour 8 personnes.", statut=statut,
    )
    db.add(devis)
    db.commit()
    db.refresh(devis)
    return devis


def test_liste_les_devis_les_plus_recents_d_abord(clean_db):
    entetes = _entetes(clean_db)
    produit = _produit(clean_db)
    _devis(clean_db, "Premier")
    _devis(clean_db, "Second", produit_id=produit.id)

    res = client.get("/api/devis", headers=entetes)

    assert res.status_code == 200
    assert [d["nom_client"] for d in res.json()] == ["Second", "Premier"]
    assert [d["nom_produit"] for d in res.json()] == ["Table en frêne", None]


def test_filtre_les_devis_par_statut(clean_db):
    entetes = _entetes(clean_db)
    _devis(clean_db, "Nouveau")
    _devis(clean_db, "Accepté", statut=StatutDevis.accepte)

    res = client.get("/api/devis?statut=accepte", headers=entetes)

    assert [d["nom_client"] for d in res.json()] == ["Accepté"]


def test_change_le_statut_d_un_devis(clean_db):
    entetes = _entetes(clean_db)
    devis = _devis(clean_db, "Jeanne")

    res = client.patch(f"/api/devis/{devis.id}/statut", json={"statut": "en_discussion"}, headers=entetes)

    assert res.status_code == 200
    assert res.json()["statut"] == "en_discussion"


def test_statut_de_devis_inconnu_refuse(clean_db):
    entetes = _entetes(clean_db)
    devis = _devis(clean_db, "Jeanne")

    res = client.patch(f"/api/devis/{devis.id}/statut", json={"statut": "oublie"}, headers=entetes)

    assert res.status_code == 422


def test_devis_inconnu_renvoie_404(clean_db):
    res = client.patch("/api/devis/999999/statut", json={"statut": "refuse"}, headers=_entetes(clean_db))

    assert res.status_code == 404
    assert res.json()["detail"] == "Devis introuvable"
