import io
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.services.devis_service import VueDevis

NOIR = colors.HexColor("#1a1a1a")
GRIS = colors.HexColor("#6b6b6b")
FILET = colors.HexColor("#d9d9d9")


def _prix(valeur: Decimal) -> str:
    entier, _, decimales = f"{Decimal(valeur):.2f}".partition(".")
    groupes = f"{int(entier):,}".replace(",", " ")
    return f"{groupes},{decimales} €"


def _date(date) -> str:
    return date.strftime("%d/%m/%Y")


def rendre_devis(vue: VueDevis) -> bytes:
    """Renders the quote as an A4 PDF. A preview (no number yet) shows APERÇU in the title."""
    base = getSampleStyleSheet()["Normal"]
    normal = ParagraphStyle("n", parent=base, fontName="Helvetica", fontSize=9, leading=12, textColor=NOIR)
    petit = ParagraphStyle("p", parent=normal, fontSize=8, leading=10, textColor=GRIS)
    titre = ParagraphStyle("t", parent=normal, fontName="Helvetica-Bold", fontSize=16, leading=20)
    droite = ParagraphStyle("d", parent=normal, alignment=TA_RIGHT)
    gras = ParagraphStyle("g", parent=normal, fontName="Helvetica-Bold")

    e = vue.entreprise
    sortie = io.BytesIO()
    document = SimpleDocTemplate(
        sortie, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm,
        bottomMargin=18 * mm, title=f"Devis {vue.numero or 'aperçu'}", pageCompression=0,
    )
    histoire = []

    entete = [Paragraph(f"<b>{e['nom_commercial']}</b>", ParagraphStyle("c", parent=titre, fontSize=13))]
    for ligne in (
        e["nom_legal"], e["adresse"], f"SIRET {e['siret']}" if e["siret"] else "",
        e["email"], e["telephone"],
    ):
        if ligne:
            entete.append(Paragraph(ligne, petit))
    histoire += entete + [Spacer(1, 8 * mm)]

    if vue.numero:
        histoire.append(Paragraph(f"Devis n° {vue.numero}" + (f" (version {vue.version})" if vue.version > 1 else ""), titre))
    else:
        histoire.append(Paragraph("APERÇU du devis (le numéro est attribué à l'envoi)", titre))
    histoire += [
        Paragraph(f"Émis le {_date(vue.emis_le)} · valable jusqu'au {_date(vue.expire_le)}", petit),
        Spacer(1, 6 * mm),
        Paragraph("<b>Client</b>", normal),
        Paragraph(vue.client_nom, normal),
    ]
    if vue.client_adresse:
        histoire.append(Paragraph(vue.client_adresse.replace("\n", "<br/>"), normal))
    histoire.append(Spacer(1, 6 * mm))

    lignes = [[Paragraph("<b>Désignation</b>", normal), Paragraph("<b>Qté</b>", droite),
               Paragraph("<b>Prix unitaire</b>", droite), Paragraph("<b>Total</b>", droite)]]
    for l in vue.lignes:
        detail = l.libelle
        if l.teinte_nom:
            detail += f"<br/><font size=8 color='#6b6b6b'>Finition : {l.teinte_nom}</font>"
        if l.souhait:
            detail += f"<br/><font size=8 color='#6b6b6b'>Souhait : {l.souhait}</font>"
        lignes.append([Paragraph(detail, normal), Paragraph(str(l.quantite), droite),
                       Paragraph(_prix(l.prix_unitaire), droite), Paragraph(_prix(l.prix_unitaire * l.quantite), droite)])
    lignes.append([Paragraph("Livraison", normal), "", "", Paragraph(_prix(vue.frais_livraison), droite)])
    lignes.append([Paragraph("<b>Total à payer</b>", normal), "", "", Paragraph(f"<b>{_prix(vue.total)}</b>", droite)])
    tableau = Table(lignes, colWidths=[95 * mm, 15 * mm, 30 * mm, 30 * mm], repeatRows=1)
    tableau.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, NOIR),
        ("LINEBELOW", (0, 1), (-1, -3), 0.3, FILET),
        ("LINEABOVE", (0, -1), (-1, -1), 0.6, NOIR),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    histoire.append(tableau)
    if e.get("mention_tva"):
        histoire += [Spacer(1, 3 * mm), Paragraph(e["mention_tva"], petit)]

    if vue.message:
        histoire += [Spacer(1, 8 * mm), Paragraph(vue.message.replace("\n", "<br/>"), normal)]
        if e.get("prenom_signature"):
            histoire += [Spacer(1, 2 * mm), Paragraph(e["prenom_signature"], gras)]

    histoire += [Spacer(1, 10 * mm), Paragraph("<b>Conditions</b>", normal)]
    for cle in ("paiement", "fabrication", "annulation"):
        if vue.conditions.get(cle):
            histoire.append(Paragraph(vue.conditions[cle], petit))
            histoire.append(Spacer(1, 1.5 * mm))

    document.build(histoire)
    return sortie.getvalue()
