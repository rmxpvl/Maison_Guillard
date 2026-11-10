from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.admin import Admin
from app.models.categorie import Categorie, Univers
from app.models.demande import Demande, StatutDemande
from app.models.produit import Produit
from app.models.teinte import Teinte
from app.services import auth_service

client = TestClient(app)
CLIENT = {"nom_client": "Jeanne Martin", "email": "jeanne@test.com", "adresse": "1 rue du Bois"}


@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()

    def vider():
        for modele in (Demande, Produit, Teinte, Categorie, Admin):
            db.query(modele).delete()
        db.commit()

    vider()
    yield db
    vider()
    db.close()


@pytest.fixture(autouse=True)
def pas_d_envoi_reel():
    with patch("app.routers.demandes.email_service.envoyer") as envoi:
        yield envoi


def _headers(db):
    db.add(Admin(email="admin@test.com", password_hash=auth_service.hash_password("test-password-123")))
    db.commit()
    return {"Authorization": f"Bearer {auth_service.login(db, 'admin@test.com', 'test-password-123')}"}


def _produit(db, nom="Table basse", prix=200, visible=True, teintes=()):
    categorie = db.query(Categorie).first()
    if categorie is None:
        categorie = Categorie(nom="Tables", slug="tables", univers=Univers.meubles)
        db.add(categorie)
        db.commit()
    produit = Produit(nom=nom, description="d", categorie_id=categorie.id, prix=prix,
                      dimensions="1x1", visible=visible, teintes=list(teintes))
    db.add(produit)
    db.commit()
    db.refresh(produit)
    return produit


def _teinte(db, nom="Charcoal", active=True):
    teinte = Teinte(nom=nom, image_url="http://x/y.png", ordre=0, active=active)
    db.add(teinte)
    db.commit()
    db.refresh(teinte)
    return teinte


def test_post_demande_enregistre_les_lignes_et_fige_prix_et_teinte(clean_db, pas_d_envoi_reel):
    teinte = _teinte(clean_db)
    produit = _produit(clean_db, prix=200, teintes=[teinte])

    res = client.post("/api/demandes", json={
        **CLIENT, "message_client": "Pour mars",
        "lignes": [{"produit_id": produit.id, "quantite": 2, "teinte_id": teinte.id, "souhait": "Plus haute"}],
    })

    assert res.status_code == 201
    body = res.json()
    assert body["statut"] == "nouvelle" and len(body["jeton"]) >= 32
    ligne = body["lignes"][0]
    assert ligne["libelle"] == "Table basse" and ligne["teinte_nom"] == "Charcoal"
    assert ligne["souhait"] == "Plus haute" and ligne["prix_indicatif"] == "200.00"
    assert ligne["prix_final"] is None
    assert body["total_indicatif"] == "400.00"
    pas_d_envoi_reel.assert_called_once()

    ligne_bdd = clean_db.query(Demande).one().lignes[0]
    assert ligne_bdd.dimensions == "1x1"  # copied for the quote, like the name and the price

    # Later price / name changes never alter the saved request.
    produit.prix, produit.nom = 999, "Autre"
    clean_db.commit()
    relu = client.get(f"/api/demandes/suivi/{body['jeton']}").json()
    assert relu["lignes"][0]["libelle"] == "Table basse"
    assert relu["lignes"][0]["prix_indicatif"] == "200.00"


def test_post_demande_refuse_un_produit_masque(clean_db):
    produit = _produit(clean_db, nom="Tabouret", visible=False)

    res = client.post("/api/demandes", json={**CLIENT, "lignes": [{"produit_id": produit.id, "quantite": 1}]})

    assert res.status_code == 422
    assert res.json()["detail"] == "« Tabouret » n'est plus disponible"
    assert clean_db.query(Demande).count() == 0


def test_post_demande_refuse_un_produit_inconnu(clean_db):
    res = client.post("/api/demandes", json={**CLIENT, "lignes": [{"produit_id": 999999, "quantite": 1}]})

    assert res.status_code == 422
    assert res.json()["detail"] == "Produit n°999999 introuvable"


def test_post_demande_refuse_une_teinte_non_proposee_ou_inactive(clean_db):
    offerte = _teinte(clean_db, "Naturel")
    inactive = _teinte(clean_db, "Vienna", active=False)
    autre = _teinte(clean_db, "Bourbon")
    produit = _produit(clean_db, nom="Banc", teintes=[offerte, inactive])

    for teinte_id in (autre.id, inactive.id):
        res = client.post("/api/demandes", json={
            **CLIENT, "lignes": [{"produit_id": produit.id, "quantite": 1, "teinte_id": teinte_id}],
        })
        assert res.status_code == 422
        assert res.json()["detail"] == "Cette finition n'est pas proposée pour « Banc »"
    assert clean_db.query(Demande).count() == 0


def test_post_demande_sans_ligne_422(clean_db):
    assert client.post("/api/demandes", json={**CLIENT, "lignes": []}).status_code == 422


def test_post_projet_libre_sans_ligne(clean_db, pas_d_envoi_reel):
    produit = _produit(clean_db)

    res = client.post("/api/demandes/projet-libre", json={
        "nom_client": "Jeanne", "email": "jeanne@test.com",
        "description_projet": "Une table de trois mètres en frêne", "produit_id": produit.id,
    })

    assert res.status_code == 201
    assert res.json()["lignes"] == []
    assert res.json()["description_projet"] == "Une table de trois mètres en frêne"
    assert res.json()["produit_reference_id"] == produit.id
    pas_d_envoi_reel.assert_called_once()


def test_post_projet_libre_produit_inconnu_422(clean_db):
    res = client.post("/api/demandes/projet-libre", json={
        "nom_client": "Jeanne", "email": "jeanne@test.com",
        "description_projet": "Une table de trois mètres", "produit_id": 999999,
    })

    assert res.status_code == 422


def test_un_envoi_d_e_mail_en_panne_ne_bloque_pas_la_demande(clean_db):
    produit = _produit(clean_db)
    with patch("app.routers.demandes.email_service.messages_nouvelle_demande", side_effect=KeyError("SMTP_HOST")):
        res = client.post("/api/demandes", json={**CLIENT, "lignes": [{"produit_id": produit.id, "quantite": 1}]})

    assert res.status_code == 201


def test_suivi_par_jeton_ne_montre_pas_les_donnees_internes(clean_db):
    produit = _produit(clean_db)
    cree = client.post("/api/demandes", json={**CLIENT, "lignes": [{"produit_id": produit.id, "quantite": 1}]}).json()

    res = client.get(f"/api/demandes/suivi/{cree['jeton']}")

    assert res.status_code == 200
    assert res.json()["id"] == cree["id"] and res.json()["statut"] == "nouvelle"
    assert "stripe_session_id" not in res.json() and "jeton" not in res.json()


def test_suivi_jeton_inconnu_404(clean_db):
    assert client.get("/api/demandes/suivi/inconnu").status_code == 404


def test_suivi_marque_un_devis_depasse_comme_expire(clean_db):
    produit = _produit(clean_db)
    cree = client.post("/api/demandes", json={**CLIENT, "lignes": [{"produit_id": produit.id, "quantite": 1}]}).json()
    demande = clean_db.query(Demande).one()
    demande.statut = StatutDemande.devis_envoye
    demande.expire_at = datetime.now(timezone.utc) - timedelta(days=1)
    clean_db.commit()

    res = client.get(f"/api/demandes/suivi/{cree['jeton']}")

    assert res.json()["statut"] == "expiree"
    clean_db.refresh(demande)
    assert demande.statut == StatutDemande.expiree


def test_liste_admin_filtre_par_statut_les_plus_recentes_d_abord(clean_db):
    produit = _produit(clean_db)
    headers = _headers(clean_db)
    for _ in range(2):
        client.post("/api/demandes", json={**CLIENT, "lignes": [{"produit_id": produit.id, "quantite": 1}]})
    derniere = clean_db.query(Demande).order_by(Demande.id.desc()).first()
    derniere.statut = StatutDemande.annulee
    clean_db.commit()

    toutes = client.get("/api/demandes", headers=headers).json()
    nouvelles = client.get("/api/demandes?statut=nouvelle", headers=headers).json()

    assert [d["id"] for d in toutes] == sorted([d["id"] for d in toutes], reverse=True)
    assert len(toutes) == 2 and len(nouvelles) == 1
    assert client.get("/api/demandes?statut=foo", headers=headers).status_code == 422


def test_detail_admin_et_404(clean_db):
    produit = _produit(clean_db)
    headers = _headers(clean_db)
    cree = client.post("/api/demandes", json={**CLIENT, "lignes": [{"produit_id": produit.id, "quantite": 1}]}).json()

    ok = client.get(f"/api/demandes/{cree['id']}", headers=headers)

    assert ok.status_code == 200 and ok.json()["email"] == "jeanne@test.com"
    assert client.get("/api/demandes/999999", headers=headers).status_code == 404


def test_changement_de_statut_respecte_les_transitions(clean_db):
    produit = _produit(clean_db)
    headers = _headers(clean_db)
    cree = client.post("/api/demandes", json={**CLIENT, "lignes": [{"produit_id": produit.id, "quantite": 1}]}).json()
    url = f"/api/demandes/{cree['id']}/statut"

    interdit = client.patch(url, json={"statut": "livree"}, headers=headers)
    ok = client.patch(url, json={"statut": "annulee"}, headers=headers)
    apres = client.patch(url, json={"statut": "nouvelle"}, headers=headers)

    assert interdit.status_code == 409
    assert ok.status_code == 200 and ok.json()["statut"] == "annulee"
    assert apres.status_code == 409
    assert client.patch("/api/demandes/999999/statut", json={"statut": "annulee"}, headers=headers).status_code == 404


def test_delete_produit_deja_demande_renvoie_409(clean_db):
    produit = _produit(clean_db)
    headers = _headers(clean_db)
    client.post("/api/demandes", json={**CLIENT, "lignes": [{"produit_id": produit.id, "quantite": 1}]})

    res = client.delete(f"/api/produits/{produit.id}", headers=headers)

    assert res.status_code == 409
    assert "masquez-le" in res.json()["detail"]


def test_delete_teinte_deja_demandee_renvoie_409(clean_db):
    teinte = _teinte(clean_db)
    produit = _produit(clean_db, teintes=[teinte])
    headers = _headers(clean_db)
    client.post("/api/demandes", json={
        **CLIENT, "lignes": [{"produit_id": produit.id, "quantite": 1, "teinte_id": teinte.id}],
    })
    # The product stops offering it, then the artisane tries to delete it.
    client.put(f"/api/produits/{produit.id}", json={"teinte_ids": []}, headers=headers)

    res = client.delete(f"/api/teintes/{teinte.id}", headers=headers)

    assert res.status_code == 409
