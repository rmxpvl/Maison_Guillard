import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.actualite import Actualite
from app.models.categorie import Categorie, Univers
from app.models.produit import Produit

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db(monkeypatch):
    monkeypatch.setenv("SITE_URL", "https://www.maison-test.fr/")
    db = SessionLocal()

    def vider():
        db.query(Actualite).delete()
        db.query(Produit).delete()
        db.query(Categorie).delete()
        db.commit()

    vider()
    yield db
    vider()
    db.close()


def _produit(db, nom, visible):
    categorie = db.query(Categorie).first()
    if categorie is None:
        categorie = Categorie(nom="Tables", slug="tables", univers=Univers.meubles)
        db.add(categorie)
        db.commit()
    produit = Produit(nom=nom, description="En chêne", categorie_id=categorie.id, prix=100,
                      dimensions="1x1x1cm", visible=visible)
    db.add(produit)
    db.commit()
    return produit


def test_sitemap_est_du_xml_avec_les_pages_fixes_et_les_univers():
    res = client.get("/api/sitemap.xml")

    assert res.status_code == 200
    assert res.headers["content-type"].startswith("application/xml")
    assert "<loc>https://www.maison-test.fr/</loc>" in res.text
    assert "<loc>https://www.maison-test.fr/boutique/ceramique</loc>" in res.text
    assert "/compte" not in res.text and "/admin" not in res.text and "/demande" not in res.text


def test_sitemap_liste_les_produits_visibles_seulement(clean_db):
    visible = _produit(clean_db, "Table", visible=True)
    masque = _produit(clean_db, "Brouillon", visible=False)

    texte = client.get("/api/sitemap.xml").text

    assert f"/produits/{visible.id}</loc>" in texte
    assert f"/produits/{masque.id}</loc>" not in texte


def test_sitemap_liste_les_actualites_publiees_seulement(clean_db):
    clean_db.add_all([
        Actualite(titre="Publiée", slug="publiee", contenu="x", publiee=True),
        Actualite(titre="Brouillon", slug="brouillon", contenu="x", publiee=False),
    ])
    clean_db.commit()

    texte = client.get("/api/sitemap.xml").text

    assert "<loc>https://www.maison-test.fr/actualites/publiee</loc><lastmod>" in texte
    assert "/actualites/brouillon" not in texte
