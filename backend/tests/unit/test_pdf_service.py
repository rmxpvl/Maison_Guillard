import io
from datetime import datetime, timezone
from decimal import Decimal

from pypdf import PdfReader

from app.services import pdf_service
from app.services.devis_service import LigneVue, VueDevis


def _vue(**extra):
    base = dict(
        numero="D-2026-0001", version=1, client_nom="Jeanne Martin", client_adresse="1 rue du Bois\n69000 Lyon",
        emis_le=datetime(2026, 11, 10, tzinfo=timezone.utc), expire_le=datetime(2026, 12, 10, tzinfo=timezone.utc),
        lignes=[LigneVue("Table basse", 2, "Charcoal", "Plus haute", Decimal("250.00"), "120 x 60 cm", "#3b3836")],
        frais_livraison=Decimal("40.00"), message="Merci pour votre confiance",
        entreprise={"nom_commercial": "Maison Guillard", "nom_legal": "EI Camille Guillard",
                    "adresse": "3 rue de l'Atelier", "siret": "123 456 789 00012", "email": "a@test.com",
                    "telephone": "04 00 00 00 00", "prenom_signature": "Camille",
                    "mention_tva": "TVA non applicable, art. 293 B du CGI"},
        conditions={"paiement": "Paiement en ligne.", "fabrication": "Sous 15 jours.", "annulation": "Remboursement total."},
        client_email="jeanne@test.com", client_telephone="06 12 34 56 78",
        demande_id=42, demande_date=datetime(2026, 11, 8, tzinfo=timezone.utc),
    )
    base.update(extra)
    return VueDevis(**base)


def _texte(pdf: bytes) -> str:
    lecteur = PdfReader(io.BytesIO(pdf))
    return "\n".join(page.extract_text() for page in lecteur.pages)


def test_vue_calcule_sous_total_et_total():
    vue = _vue()

    assert vue.sous_total == Decimal("500.00")
    assert vue.total == Decimal("540.00")  # 2 x 250 + 40 de livraison


def test_numero_affiche_ajoute_la_version_a_partir_de_la_deuxieme():
    assert _vue().numero_affiche == "D-2026-0001"
    assert _vue(version=2).numero_affiche == "D-2026-0001-v2"
    assert _vue(numero=None).numero_affiche is None


def test_pdf_reprend_les_blocs_de_la_maquette():
    texte = _texte(pdf_service.rendre_devis(_vue()))

    for attendu in (
        "D-2026-0001", "10 novembre 2026", "10 décembre 2026", "Jeanne Martin", "jeanne@test.com",
        "Demande n°42 du 8 novembre 2026", "Table basse", "120 x 60 cm", "Finition Charcoal",
        "Plus haute", "500,00 €", "40,00 €", "540,00 €", "TVA non applicable, art. 293 B du CGI",
        "Merci pour votre confiance", "Camille", "Paiement en ligne.", "Sous 15 jours.",
        "Remboursement total.", "Bon pour accord", "EI Camille Guillard", "123 456 789 00012",
        "Page 1 / 1", "04 00 00 00 00",
    ):
        assert attendu in texte, attendu


def test_pdf_est_un_pdf_a_la_police_du_site():
    pdf = pdf_service.rendre_devis(_vue())

    assert pdf.startswith(b"%PDF")
    assert b"Jost" in pdf


def test_pdf_d_une_version_ulterieure_porte_le_suffixe():
    assert "D-2026-0001-v2" in _texte(pdf_service.rendre_devis(_vue(version=2)))


def test_pdf_d_apercu_sans_numero():
    texte = _texte(pdf_service.rendre_devis(_vue(numero=None)))

    assert "APERÇU" in texte
    assert "D-2026" not in texte


def test_pdf_apres_acceptation_montre_la_date_et_les_cgv():
    vue = _vue(accepte_le=datetime(2026, 11, 12, 14, 30, tzinfo=timezone.utc), cgv_version="1")

    texte = _texte(pdf_service.rendre_devis(vue))

    assert "12/11/2026" in texte
    assert "version 1" in texte


def test_un_long_devis_passe_sur_plusieurs_pages_avec_la_pagination():
    lignes = [LigneVue(f"Pièce {i}", 1, None, None, Decimal("10.00"), "10 cm") for i in range(60)]

    pdf = pdf_service.rendre_devis(_vue(lignes=lignes))

    lecteur = PdfReader(io.BytesIO(pdf))
    assert len(lecteur.pages) > 1
    assert f"Page 1 / {len(lecteur.pages)}" in lecteur.pages[0].extract_text()
    assert f"Page {len(lecteur.pages)} / {len(lecteur.pages)}" in lecteur.pages[-1].extract_text()


def test_une_ligne_sans_teinte_ni_dimensions_ne_plante_pas():
    vue = _vue(lignes=[LigneVue("Carnet", 1, None, None, Decimal("16.00"))], message=None, client_adresse=None)

    assert "Carnet" in _texte(pdf_service.rendre_devis(vue))
