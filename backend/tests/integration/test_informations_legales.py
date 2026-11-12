import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.parametre import Parametre

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()
    db.query(Parametre).delete()
    db.commit()
    yield db
    db.query(Parametre).delete()
    db.commit()
    db.close()


def test_informations_legales_publiques_avec_la_version_des_cgv(clean_db):
    clean_db.add(Parametre(
        id=1, nom_commercial="Maison Guillard", nom_legal="EI Camille Guillard", adresse="3 rue de l'Atelier, 69000 Lyon",
        siret="123 456 789 00012", email="atelier@test.com", telephone="04 00 00 00 00", mention_tva="TVA non applicable",
    ))
    clean_db.commit()

    res = client.get("/api/informations-legales")

    assert res.status_code == 200
    assert res.json() == {
        "nom_commercial": "Maison Guillard", "nom_legal": "EI Camille Guillard",
        "adresse": "3 rue de l'Atelier, 69000 Lyon", "siret": "123 456 789 00012",
        "email": "atelier@test.com", "telephone": "04 00 00 00 00", "mention_tva": "TVA non applicable",
        "cgv_version": "1",
    }


def test_informations_vides_tant_que_l_artisane_n_a_rien_rempli():
    body = client.get("/api/informations-legales").json()

    assert body["nom_legal"] == "" and body["siret"] == "" and body["cgv_version"] == "1"


def test_ne_renvoie_aucun_reglage_interne(clean_db):
    clean_db.add(Parametre(id=1, frais_meubles=60, cond_paiement="secret interne"))
    clean_db.commit()

    body = client.get("/api/informations-legales").json()

    assert set(body) == {"nom_commercial", "nom_legal", "adresse", "siret", "email", "telephone", "mention_tva", "cgv_version"}
