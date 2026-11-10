import io
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import BaseDocTemplate, Flowable, Frame, KeepTogether, PageTemplate, Paragraph, Spacer, Table, TableStyle
from svglib.svglib import svg2rlg

from app.services.devis_service import LigneVue, VueDevis

# Layout of the validated mockup (docs/specs/maquettes-v2/devis-pdf-apercu.html): A4, the site's
# black and white style and its Jost typeface.
ASSETS = Path(__file__).resolve().parent.parent / "assets"
PARIS = ZoneInfo("Europe/Paris")
INK = colors.HexColor("#2a2622")
GRIS = colors.HexColor("#8a7d6b")
GRIS_TEXTE = colors.HexColor("#6b5f50")
FILET = colors.HexColor("#e2d6c2")
FOND = colors.HexColor("#f0e6d6")
PAPIER = colors.HexColor("#faf6ef")  # page background: warm cream, like the oak of the pieces

LIGHT, REGULAR, MEDIUM, ITALIC = "Jost-Light", "Jost-Regular", "Jost-Medium", "Jost-LightItalic"
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]

_polices_enregistrees = False


def _polices() -> None:
    global _polices_enregistrees
    if _polices_enregistrees:
        return
    for nom in (LIGHT, REGULAR, MEDIUM, ITALIC):
        pdfmetrics.registerFont(TTFont(nom, str(ASSETS / "fonts" / f"{nom}.ttf")))
    pdfmetrics.registerFontFamily("Jost", normal=LIGHT, bold=MEDIUM, italic=ITALIC, boldItalic=MEDIUM)
    _polices_enregistrees = True


def _prix(valeur: Decimal) -> str:
    entier, _, decimales = f"{Decimal(valeur):.2f}".partition(".")
    return f"{int(entier):,}".replace(",", " ") + f",{decimales} €"


def _paris(date: datetime) -> datetime:
    return date.astimezone(PARIS)


def _date_longue(date: datetime) -> str:
    d = _paris(date)
    jour = "1er" if d.day == 1 else str(d.day)
    return f"{jour} {MOIS[d.month - 1]} {d.year}"


def _style(nom: str, police: str = LIGHT, taille: float = 9.75, couleur=INK, **extra) -> ParagraphStyle:
    return ParagraphStyle(nom, fontName=police, fontSize=taille, leading=extra.pop("leading", taille * 1.45), textColor=couleur, **extra)


class Espace(Flowable):
    """One line of letter-spaced text (Paragraph cannot space letters)."""

    def __init__(self, texte, police, taille, couleur=INK, espace=0.0, droite=False):
        super().__init__()
        self.texte, self.police, self.taille, self.couleur = texte, police, taille, couleur
        self.espace, self.droite = espace, droite

    def wrap(self, largeur, hauteur):
        self._largeur = largeur
        return largeur, self.taille * 1.4

    def draw(self):
        largeur_texte = stringWidth(self.texte, self.police, self.taille) + self.espace * len(self.texte)
        x = self._largeur - largeur_texte if self.droite else 0
        t = self.canv.beginText()
        t.setFont(self.police, self.taille)
        t.setFillColor(self.couleur)
        t.setCharSpace(self.espace)
        t.setTextOrigin(x, self.taille * 0.3)
        t.textOut(self.texte)
        self.canv.drawText(t)


class _CanvasPagine(canvas.Canvas):
    """Draws the footer once the page count is known: « Page 1 / 3 »."""

    def __init__(self, *args, pied: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self._pied = pied
        self._etats = []

    def showPage(self):
        self._etats.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._etats)
        for etat in self._etats:
            self.__dict__.update(etat)
            self._dessiner_pied(total)
            super().showPage()
        super().save()

    def _dessiner_pied(self, total: int):
        gauche, droite = 48, A4[0] - 48
        self.setStrokeColor(FILET)
        self.setLineWidth(0.6)
        self.line(gauche, 40, droite, 40)
        self.setFillColor(colors.HexColor("#9a8c78"))
        self.setFont(LIGHT, 7.5)
        self.drawString(gauche, 28, self._pied)
        self.drawRightString(droite, 28, f"Page {self._pageNumber} / {total}")


def _fond(canvas_, _document) -> None:
    canvas_.saveState()
    canvas_.setFillColor(PAPIER)
    canvas_.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)
    canvas_.restoreState()


def _logo(hauteur: float) -> Drawing:
    dessin = svg2rlg(str(ASSETS / "logo.svg"))
    echelle = hauteur / dessin.height
    dessin.scale(echelle, echelle)
    dessin.width, dessin.height = dessin.width * echelle, dessin.height * echelle
    return dessin


def _detail(ligne: LigneVue, style: ParagraphStyle):
    """« 120 x 60 cm · [swatch] Finition Charcoal » on one line."""
    cellules, largeurs = [], []
    if ligne.dimensions:
        texte = escape(ligne.dimensions) + (" · " if ligne.teinte_nom else "")
        cellules.append(Paragraph(texte, style))
        largeurs.append(stringWidth(ligne.dimensions + (" · " if ligne.teinte_nom else ""), LIGHT, style.fontSize) + 2)
    if ligne.teinte_nom:
        if ligne.teinte_couleur:
            pastille = Drawing(10, 9)
            pastille.add(Rect(0, 0, 8, 8, fillColor=colors.HexColor(ligne.teinte_couleur),
                              strokeColor=colors.HexColor("#c9b99d"), strokeWidth=0.5))
            cellules.append(pastille)
            largeurs.append(11)
        etiquette = f"Finition {ligne.teinte_nom}"
        cellules.append(Paragraph(escape(etiquette), style))
        largeurs.append(stringWidth(etiquette, LIGHT, style.fontSize) + 4)
    if not cellules:
        return None
    tableau = Table([cellules], colWidths=largeurs, hAlign="LEFT")
    tableau.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return tableau


def rendre_devis(vue: VueDevis) -> bytes:
    """Renders the quote as an A4 PDF. A preview (no number yet) is marked APERÇU."""
    _polices()
    e = vue.entreprise
    largeur = A4[0] - 96  # 48 pt margins
    normal = _style("normal")
    droite = _style("droite", alignment=TA_RIGHT)
    doux = _style("doux", taille=8.6, couleur=colors.HexColor("#5e5346"), alignment=TA_RIGHT)
    detail = _style("detail", taille=8.6, couleur=GRIS_TEXTE)
    souhait = _style("souhait", ITALIC, 8.6, GRIS_TEXTE)
    petit = _style("petit", taille=8.6, couleur=colors.HexColor("#4a4036"))
    etiquette = lambda texte, **k: Espace(texte, REGULAR, 7.5, GRIS, 1.2, **k)  # noqa: E731

    histoire = []

    # --- header: brand + workshop details
    marque = Table(
        [[_logo(14 * mm), [
            Espace((e["nom_commercial"] or "Maison Guillard").upper(), REGULAR, 16.5, INK, 3.6),
            Spacer(1, 2),
            Espace("ATELIER · MOBILIER, CÉRAMIQUE, PAPETERIE", REGULAR, 7.6, GRIS, 1.1),
        ]]],
        colWidths=[19 * mm, None],
    )
    marque.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
    atelier = [escape(x) for x in (e["adresse"], e["email"], e["telephone"]) if x]
    entete = Table(
        [[marque, Paragraph("<br/>".join(a.replace("\n", "<br/>") for a in atelier), doux)]],
        colWidths=[largeur * 0.62, largeur * 0.38],
    )
    entete.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, INK),
    ]))
    histoire.append(entete)

    # --- title + number / dates
    if vue.numero:
        numero = f"<font name='{MEDIUM}' size='10.5'>N° {escape(vue.numero_affiche)}</font>"
    else:
        numero = f"<font name='{MEDIUM}' size='10.5'>APERÇU</font> · numéro attribué à l'envoi"
    bloc_numero = Paragraph(
        f"{numero}<br/>Émis le {_date_longue(vue.emis_le)}<br/>Valable jusqu'au "
        f"<font name='{MEDIUM}'>{_date_longue(vue.expire_le)}</font>",
        _style("numero", taille=9, alignment=TA_RIGHT, leading=13),
    )
    titre = Table([[Espace("DEVIS", LIGHT, 25.5, INK, 7.6), bloc_numero]], colWidths=[largeur * 0.5, largeur * 0.5])
    titre.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 22), ("BOTTOMPADDING", (0, 0), (-1, -1), 18),
    ]))
    histoire.append(titre)

    # --- client / request
    client = f"<font name='{MEDIUM}'>{escape(vue.client_nom)}</font>"
    if vue.client_adresse:
        client += "<br/>" + escape(vue.client_adresse).replace("\n", "<br/>")
    contact = " · ".join(x for x in (vue.client_email, vue.client_telephone) if x)
    if contact:
        client += "<br/>" + escape(contact)
    demande = "Livraison à l'adresse ci-contre"
    if vue.demande_id is not None:
        demande = f"Demande n°{vue.demande_id}"
        if vue.demande_date:
            demande += f" du {_date_longue(vue.demande_date)}"
        demande += "<br/>Livraison à l'adresse ci-contre"
    blocs = Table(
        [[[etiquette("CLIENT"), Spacer(1, 4), Paragraph(client, normal)],
          [etiquette("VOTRE DEMANDE"), Spacer(1, 4), Paragraph(demande, normal)]]],
        colWidths=[largeur / 2, largeur / 2],
    )
    blocs.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 18), ("TOPPADDING", (0, 0), (-1, -1), 0)]))
    histoire.append(blocs)

    # --- lines
    lignes = [[etiquette("DÉSIGNATION"), Espace("QTÉ", REGULAR, 7.5, GRIS, 1.0, droite=True),
               Espace("PRIX UNITAIRE", REGULAR, 7.5, GRIS, 1.0, droite=True),
               Espace("TOTAL", REGULAR, 7.5, GRIS, 1.0, droite=True)]]
    for l in vue.lignes:
        cellule = [Paragraph(escape(l.libelle), _style("piece", REGULAR, 10.5))]
        sous_ligne = _detail(l, detail)
        if sous_ligne is not None:
            cellule += [Spacer(1, 2), sous_ligne]
        if l.souhait:
            cellule += [Spacer(1, 2), Paragraph(f"Votre souhait : « {escape(l.souhait)} »", souhait)]
        lignes.append([cellule, Paragraph(str(l.quantite), droite), Paragraph(_prix(l.prix_unitaire), droite),
                       Paragraph(_prix(l.prix_unitaire * l.quantite), droite)])
    tableau = Table(lignes, colWidths=[largeur - 28 - 85 - 85, 28, 85, 85], repeatRows=1)
    tableau.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, INK), ("LINEBELOW", (0, 1), (-1, -1), 0.4, FILET),
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, 0), 4), ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 1), (-1, -1), 9), ("BOTTOMPADDING", (0, 1), (-1, -1), 9),
    ]))
    histoire += [tableau, Spacer(1, 8)]

    # --- totals + VAT
    gros = _style("gros", REGULAR, 12.75, alignment=TA_RIGHT)
    totaux = Table(
        [[Paragraph("Sous-total", normal), Paragraph(_prix(vue.sous_total), droite)],
         [Paragraph("Livraison", normal), Paragraph(_prix(vue.frais_livraison), droite)],
         [Paragraph("Total à régler", _style("grand", REGULAR, 12.75)), Paragraph(_prix(vue.total), gros)]],
        colWidths=[140, 85], hAlign="RIGHT",
    )
    totaux.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LINEABOVE", (0, 2), (-1, 2), 0.8, INK), ("TOPPADDING", (0, 2), (-1, 2), 9),
    ]))
    fin_tableau = [totaux]
    if e.get("mention_tva"):
        fin_tableau += [Spacer(1, 4), Paragraph(escape(e["mention_tva"]), _style("tva", taille=8.25, couleur=GRIS, alignment=TA_RIGHT))]
    histoire.append(KeepTogether(fin_tableau))

    # --- the workshop's word
    if vue.message:
        texte = escape(vue.message).replace("\n", "<br/>")
        if e.get("prenom_signature"):
            texte += f" — <font name='{MEDIUM}'>{escape(e['prenom_signature'])}</font>"
        mot = Table([[[etiquette("LE MOT DE L'ATELIER"), Spacer(1, 4), Paragraph(texte, _style("mot", taille=9.4, leading=13.5))]]],
                    colWidths=[largeur])
        mot.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), FOND), ("LEFTPADDING", (0, 0), (-1, -1), 13),
                                 ("RIGHTPADDING", (0, 0), (-1, -1), 13), ("TOPPADDING", (0, 0), (-1, -1), 12),
                                 ("BOTTOMPADDING", (0, 0), (-1, -1), 12)]))
        histoire += [Spacer(1, 20), KeepTogether([mot])]

    # --- three conditions
    titres = {"paiement": "Paiement", "fabrication": "Fabrication et livraison", "annulation": "Annulation"}
    colonnes = [[Paragraph(f"<font name='{MEDIUM}'>{titres[cle]}</font>", _style("ct", taille=9)),
                 Spacer(1, 2), Paragraph(escape(vue.conditions.get(cle, "")), petit)] for cle in titres]
    conditions = Table([colonnes], colWidths=[largeur / 3] * 3)
    conditions.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                    ("RIGHTPADDING", (0, 0), (-1, -1), 12)]))
    histoire += [Spacer(1, 20), KeepTogether([conditions])]

    # --- "bon pour accord"
    if vue.accepte_le:
        moment = _paris(vue.accepte_le)
        gauche = f"<font name='{MEDIUM}'>Bon pour accord</font> — accepté en ligne le {moment:%d/%m/%Y} à {moment:%H:%M}"
    else:
        gauche = f"<font name='{MEDIUM}'>Bon pour accord</font> — à accepter en ligne depuis la page de votre devis"
    cgv = (f"Conditions générales de vente (version {escape(vue.cgv_version)}) acceptées"
           if vue.cgv_version else "Conditions générales de vente à accepter")
    accord = Table([[Paragraph(gauche, _style("ag", taille=8.6, couleur=GRIS_TEXTE)),
                     Paragraph(cgv, _style("ad", taille=8.6, couleur=GRIS_TEXTE, alignment=TA_RIGHT))]],
                   colWidths=[largeur * 0.58, largeur * 0.42])
    accord.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#b3a285"), None, (2, 2)),
                                ("LEFTPADDING", (0, 0), (-1, -1), 13), ("RIGHTPADDING", (0, 0), (-1, -1), 13),
                                ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                                ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    histoire += [Spacer(1, 20), KeepTogether([accord])]

    # --- footer text (legal identity), page numbers added at save time
    pied = " · ".join(x for x in (
        e.get("nom_commercial"), e.get("nom_legal"), f"SIRET {e['siret']}" if e.get("siret") else None,
    ) if x)

    sortie = io.BytesIO()
    document = BaseDocTemplate(
        sortie, pagesize=A4, leftMargin=48, rightMargin=48, topMargin=42, bottomMargin=54,
        title=f"Devis {vue.numero_affiche}" if vue.numero else "Aperçu du devis", author=e.get("nom_commercial") or "Maison Guillard",
    )
    cadre = Frame(48, 54, largeur, A4[1] - 54 - 42, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    document.addPageTemplates([PageTemplate(id="devis", frames=[cadre], onPage=_fond)])
    document.build(histoire, canvasmaker=lambda *a, **k: _CanvasPagine(*a, pied=pied, **k))
    return sortie.getvalue()
