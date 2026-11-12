from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.admin import Admin
from app.models.categorie import Categorie, Univers
from app.models.demande import Demande, StatutDemande
from app.models.devis_numero import CompteurDevis
from app.models.message_type import MessageType
from app.models.parametre import Parametre
from app.models.produit import Produit
from app.services import auth_service

client = TestClient(app)
ANNEE = datetime.now(timezone.utc).year
CLIENT = {"nom_client": "Jeanne Martin", "email": "jeanne@test.com", "adresse": "1 rue du Bois"}
REGLAGES = {
    "nom_commercial": "Maison Guillard", "nom_legal": "EI Camille Guillard",
    "adresse": "3 rue de l'Atelier, 69000 Lyon", "siret": "123 456 789 00012", "email": "atelier@test.com",
    "telephone": "04 00 00 00 00", "prenom_signature": "Camille",
    "mention_tva": "TVA non applicable, art. 293 B du CGI", "validite_jours": 30,
    "frais_meubles": "60.00", "frais_ceramique": "15.00", "frais_papeterie": "5.00",
    "cond_paiement": "Paiement en ligne.", "cond_fabrication": "Fabrication sous 15 jours.",
    "cond_annulation": "Remboursement total avant fabrication.",
}


@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()

    def vider():
        for modele in (Demande, Produit, Categorie, MessageType, Parametre, CompteurDevis, Admin):
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


@pytest.fixture
def admin(clean_db):
    clean_db.add(Admin(email="admin@test.com", password_hash=auth_service.hash_password("test-password-123")))
    clean_db.commit()
    return {"Authorization": f"Bearer {auth_service.login(clean_db, 'admin@test.com', 'test-password-123')}"}


def _reglages_complets(admin):
    assert client.put("/api/reglages-devis", json=REGLAGES, headers=admin).status_code == 200


def _produit(db, nom="Table basse", prix=200, univers=Univers.meubles):
    slug = f"cat-{univers.value}"
    categorie = db.query(Categorie).filter(Categorie.slug == slug).first()
    if categorie is None:
        categorie = Categorie(nom=univers.value, slug=slug, univers=univers)
        db.add(categorie)
        db.commit()
    produit = Produit(nom=nom, description="d", categorie_id=categorie.id, prix=prix, dimensions="1x1")
    db.add(produit)
    db.commit()
    return produit


def _demande(db, *produits):
    corps = {**CLIENT, "lignes": [{"produit_id": p.id, "quantite": 2} for p in produits]}
    return client.post("/api/demandes", json=corps).json()


def _envoi(demande, prix="250.00", **extra):
    corps = {
        "lignes": [{"id": l["id"], "prix_final": prix} for l in demande["lignes"]],
        "lignes_libres": [], "frais_livraison": "40.00", "message_artisane": "Merci",
    }
    corps.update(extra)
    return corps


# ---------- réglages et messages types ----------

def test_reglages_par_defaut_puis_modification(admin):
    initial = client.get("/api/reglages-devis", headers=admin).json()
    assert initial["nom_legal"] == "" and initial["validite_jours"] == 30
    assert "15 jours" in initial["cond_fabrication"]

    _reglages_complets(admin)

    relu = client.get("/api/reglages-devis", headers=admin).json()
    assert relu["siret"] == "123 456 789 00012" and relu["frais_meubles"] == "60.00"


def test_reglages_refusent_une_validite_nulle(admin):
    assert client.put("/api/reglages-devis", json={**REGLAGES, "validite_jours": 0}, headers=admin).status_code == 422


def test_messages_types_crud(admin):
    cree = client.post("/api/messages-types", json={"titre": "Délai", "texte": "Fabrication sous 15 jours."}, headers=admin)
    assert cree.status_code == 201
    mid = cree.json()["id"]

    modif = client.put(f"/api/messages-types/{mid}", json={"titre": "Délai", "texte": "Sous 15 jours."}, headers=admin)
    assert modif.json()["texte"] == "Sous 15 jours."
    assert [m["id"] for m in client.get("/api/messages-types", headers=admin).json()] == [mid]
    assert client.delete(f"/api/messages-types/{mid}", headers=admin).status_code == 204
    assert client.delete(f"/api/messages-types/{mid}", headers=admin).status_code == 404
    assert client.put("/api/messages-types/999999", json={"titre": "a", "texte": "b"}, headers=admin).status_code == 404


# ---------- envoi du devis ----------

def test_envoyer_le_devis_fige_prix_numero_expiration_et_previent_le_client(clean_db, admin, pas_d_envoi_reel):
    _reglages_complets(admin)
    demande = _demande(clean_db, _produit(clean_db))
    pas_d_envoi_reel.reset_mock()

    res = client.post(f"/api/demandes/{demande['id']}/devis", json=_envoi(demande), headers=admin)

    assert res.status_code == 200
    d = res.json()
    assert d["statut"] == "devis_envoye" and d["numero_devis"] == f"D-{ANNEE}-0001" and d["version_devis"] == 1
    assert d["lignes"][0]["prix_final"] == "250.00" and d["frais_livraison"] == "40.00"
    assert d["total_final"] == "540.00" and d["message_artisane"] == "Merci"
    expire = datetime.fromisoformat(d["expire_at"])
    assert timedelta(days=29) < expire - datetime.now(timezone.utc) <= timedelta(days=30)

    pas_d_envoi_reel.assert_called_once()
    (messages,), _ = pas_d_envoi_reel.call_args
    assert len(messages) == 1 and messages[0]["To"] == "jeanne@test.com"
    pieces = list(messages[0].iter_attachments())
    assert pieces[0].get_filename() == f"devis-D-{ANNEE}-0001.pdf"
    assert pieces[0].get_content_type() == "application/pdf"
    assert f"/devis/{clean_db.query(Demande).one().jeton}" in messages[0].get_body().get_content()


def test_envoyer_refuse_tant_que_les_mentions_obligatoires_manquent(clean_db, admin):
    demande = _demande(clean_db, _produit(clean_db))

    res = client.post(f"/api/demandes/{demande['id']}/devis", json=_envoi(demande), headers=admin)

    assert res.status_code == 422
    assert res.json()["detail"] == "Réglages du devis incomplets : nom légal, adresse, SIRET, e-mail"
    assert clean_db.query(Demande).one().statut == StatutDemande.nouvelle


def test_renvoyer_garde_le_numero_monte_la_version_et_remplace_les_lignes_libres(clean_db, admin):
    _reglages_complets(admin)
    demande = _demande(clean_db, _produit(clean_db))
    libre = {"libelle": "Supplément ponçage", "prix": "30.00", "quantite": 1}
    client.post(f"/api/demandes/{demande['id']}/devis", json=_envoi(demande, lignes_libres=[libre]), headers=admin)

    res = client.post(f"/api/demandes/{demande['id']}/devis", json=_envoi(demande, prix="300.00"), headers=admin)

    d = res.json()
    assert res.status_code == 200
    assert d["numero_devis"] == f"D-{ANNEE}-0001" and d["version_devis"] == 2
    assert [l["libelle"] for l in d["lignes"]] == ["Table basse"]  # the old free line is gone
    assert d["lignes"][0]["prix_final"] == "300.00"


def test_numeros_successifs_sans_doublon(clean_db, admin):
    _reglages_complets(admin)
    numeros = []
    for nom in ("A", "B"):
        demande = _demande(clean_db, _produit(clean_db, nom=nom))
        numeros.append(client.post(f"/api/demandes/{demande['id']}/devis", json=_envoi(demande), headers=admin).json()["numero_devis"])

    assert numeros == [f"D-{ANNEE}-0001", f"D-{ANNEE}-0002"]


def test_envoyer_refuse_une_demande_deja_payee(clean_db, admin):
    _reglages_complets(admin)
    demande = _demande(clean_db, _produit(clean_db))
    d = clean_db.query(Demande).one()
    d.statut = StatutDemande.payee
    clean_db.commit()

    res = client.post(f"/api/demandes/{demande['id']}/devis", json=_envoi(demande), headers=admin)

    assert res.status_code == 409


def test_envoyer_refuse_une_ligne_etrangere_ou_un_prix_manquant(clean_db, admin):
    _reglages_complets(admin)
    demande = _demande(clean_db, _produit(clean_db))
    etranger = _envoi(demande, lignes=[{"id": 999999, "prix_final": "10.00"}])
    manquant = _envoi(demande, lignes=[])

    assert client.post(f"/api/demandes/{demande['id']}/devis", json=etranger, headers=admin).status_code == 422
    assert client.post(f"/api/demandes/{demande['id']}/devis", json=manquant, headers=admin).status_code == 422
    assert clean_db.query(Demande).one().statut == StatutDemande.nouvelle


def test_projet_libre_se_chiffre_avec_une_ligne_libre(clean_db, admin):
    _reglages_complets(admin)
    libre = client.post("/api/demandes/projet-libre", json={
        "nom_client": "Jeanne", "email": "jeanne@test.com", "description_projet": "Une table de trois mètres en frêne",
    }).json()
    sans_ligne = {"lignes": [], "lignes_libres": [], "frais_livraison": "0", "message_artisane": None}
    avec = {**sans_ligne, "lignes_libres": [{"libelle": "Table en frêne 3 m", "prix": "1800.00", "quantite": 1}]}

    assert client.post(f"/api/demandes/{libre['id']}/devis", json=sans_ligne, headers=admin).status_code == 422
    res = client.post(f"/api/demandes/{libre['id']}/devis", json=avec, headers=admin)

    assert res.status_code == 200
    assert res.json()["total_final"] == "1800.00"
    assert res.json()["lignes"][0]["produit_id"] is None


def test_frais_de_livraison_suggeres_depuis_les_univers(clean_db, admin):
    _reglages_complets(admin)
    demande = _demande(clean_db, _produit(clean_db, "T"), _produit(clean_db, "V", univers=Univers.ceramique))

    detail = client.get(f"/api/demandes/{demande['id']}", headers=admin).json()

    assert detail["frais_livraison_suggere"] == "60.00"  # highest of meubles / céramique


# ---------- aperçu et PDF ----------

def test_apercu_renvoie_un_pdf_sans_rien_enregistrer(clean_db, admin):
    _reglages_complets(admin)
    demande = _demande(clean_db, _produit(clean_db))

    res = client.post(f"/api/demandes/{demande['id']}/devis/apercu", json=_envoi(demande), headers=admin)

    assert res.status_code == 200 and res.headers["content-type"] == "application/pdf"
    assert res.content.startswith(b"%PDF")
    d = clean_db.query(Demande).one()
    assert d.statut == StatutDemande.nouvelle and d.numero_devis is None


def test_pdf_du_devis_envoye_pour_l_admin_et_pour_le_client(clean_db, admin):
    _reglages_complets(admin)
    demande = _demande(clean_db, _produit(clean_db))
    jeton = clean_db.query(Demande).one().jeton
    assert client.get(f"/api/demandes/{demande['id']}/devis.pdf", headers=admin).status_code == 404
    assert client.get(f"/api/demandes/suivi/{jeton}/devis.pdf").status_code == 404
    client.post(f"/api/demandes/{demande['id']}/devis", json=_envoi(demande), headers=admin)

    pour_admin = client.get(f"/api/demandes/{demande['id']}/devis.pdf", headers=admin)
    pour_client = client.get(f"/api/demandes/suivi/{jeton}/devis.pdf")

    assert pour_admin.status_code == 200 and pour_admin.content.startswith(b"%PDF")
    assert pour_client.status_code == 200 and f"D-{ANNEE}-0001".encode() in pour_client.content


# ---------- côté client ----------

def test_le_client_voit_son_devis_et_les_coordonnees_de_l_atelier(clean_db, admin):
    _reglages_complets(admin)
    demande = _demande(clean_db, _produit(clean_db))
    client.post(f"/api/demandes/{demande['id']}/devis", json=_envoi(demande), headers=admin)
    jeton = clean_db.query(Demande).one().jeton

    vu = client.get(f"/api/demandes/suivi/{jeton}").json()

    assert vu["statut"] == "devis_envoye" and vu["total_final"] == "540.00"
    assert vu["lignes"][0]["prix_final"] == "250.00" and vu["message_artisane"] == "Merci"
    assert vu["atelier_email"] == "atelier@test.com" and vu["atelier_telephone"] == "04 00 00 00 00"
    assert "email" not in vu and "jeton" not in vu


def test_le_client_peut_refuser_un_devis_valide(clean_db, admin, pas_d_envoi_reel):
    _reglages_complets(admin)
    demande = _demande(clean_db, _produit(clean_db))
    client.post(f"/api/demandes/{demande['id']}/devis", json=_envoi(demande), headers=admin)
    jeton = clean_db.query(Demande).one().jeton
    pas_d_envoi_reel.reset_mock()

    res = client.post(f"/api/demandes/suivi/{jeton}/refuser")

    assert res.status_code == 200 and res.json()["statut"] == "refusee"
    (messages,), _ = pas_d_envoi_reel.call_args
    assert messages[0]["Subject"] == f"Devis D-{ANNEE}-0001 refusé par le client"
    assert client.post(f"/api/demandes/suivi/{jeton}/refuser").status_code == 409


def test_refuser_impossible_sans_devis_ou_apres_expiration(clean_db, admin):
    _reglages_complets(admin)
    demande = _demande(clean_db, _produit(clean_db))
    jeton = clean_db.query(Demande).one().jeton
    assert client.post(f"/api/demandes/suivi/{jeton}/refuser").status_code == 409  # nouvelle

    client.post(f"/api/demandes/{demande['id']}/devis", json=_envoi(demande), headers=admin)
    d = clean_db.query(Demande).one()
    d.expire_at = datetime.now(timezone.utc) - timedelta(days=1)
    clean_db.commit()

    assert client.post(f"/api/demandes/suivi/{jeton}/refuser").status_code == 409
    assert client.post("/api/demandes/suivi/inconnu/refuser").status_code == 404


def test_renvoyer_un_devis_expire_le_remet_en_vigueur(clean_db, admin):
    _reglages_complets(admin)
    demande = _demande(clean_db, _produit(clean_db))
    client.post(f"/api/demandes/{demande['id']}/devis", json=_envoi(demande), headers=admin)
    d = clean_db.query(Demande).one()
    d.expire_at = datetime.now(timezone.utc) - timedelta(days=1)
    clean_db.commit()

    res = client.post(f"/api/demandes/{demande['id']}/devis", json=_envoi(demande), headers=admin)

    assert res.status_code == 200 and res.json()["statut"] == "devis_envoye" and res.json()["version_devis"] == 2
