from datetime import datetime, timezone
from decimal import Decimal

from app.services import pdf_service
from app.services.devis_service import LigneVue, VueDevis


def _vue(**extra):
    base = dict(
        numero="D-2026-0001", version=1, client_nom="Jeanne Martin", client_adresse="1 rue du Bois",
        emis_le=datetime(2026, 11, 10, tzinfo=timezone.utc), expire_le=datetime(2026, 12, 10, tzinfo=timezone.utc),
        lignes=[LigneVue("Table basse", 2, "Charcoal", "Plus haute", Decimal("250.00"))],
        frais_livraison=Decimal("40.00"), message="Merci pour votre confiance",
        entreprise={"nom_commercial": "Maison Guillard", "nom_legal": "EI Camille Guillard",
                    "adresse": "3 rue de l'Atelier", "siret": "123 456 789 00012", "email": "a@test.com",
                    "telephone": "", "prenom_signature": "Camille", "mention_tva": "TVA non applicable, art. 293 B du CGI"},
        conditions={"paiement": "Paiement en ligne.", "fabrication": "Sous 15 jours.", "annulation": "Remboursement total."},
    )
    base.update(extra)
    return VueDevis(**base)


def test_vue_calcule_le_total():
    assert _vue().total == Decimal("540.00")  # 2 x 250 + 40 de livraison


def test_pdf_est_un_pdf_qui_contient_le_numero_et_le_total():
    pdf = pdf_service.rendre_devis(_vue())

    assert pdf.startswith(b"%PDF")
    assert b"D-2026-0001" in pdf
    assert b"540,00" in pdf


def test_pdf_d_apercu_sans_numero():
    pdf = pdf_service.rendre_devis(_vue(numero=None))

    assert pdf.startswith(b"%PDF")
    assert b"D-2026-0001" not in pdf
