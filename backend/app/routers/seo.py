import os
from xml.sax.saxutils import escape

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.actualite import Actualite
from app.models.categorie import Univers
from app.models.produit import Produit

router = APIRouter(prefix="/api", tags=["Référencement"])

# Public pages worth indexing. Account, request, quote and admin pages are left out (robots.txt too).
PAGES_FIXES = ["/", "/boutique", "/actualites", "/qui-sommes-nous", "/contact",
               "/cgv", "/mentions-legales", "/confidentialite"]


def _url(site: str, chemin: str, lastmod: str | None = None) -> str:
    date = f"<lastmod>{lastmod}</lastmod>" if lastmod else ""
    return f"<url><loc>{escape(site + chemin)}</loc>{date}</url>"


@router.get("/sitemap.xml", summary="Plan du site pour les moteurs de recherche", response_class=Response)
def sitemap(db: Session = Depends(get_db)):
    """Built on each call from the database: a product put online or a post published shows up
    without any redeploy. Only what a visitor can see: visible products, published posts."""
    site = os.environ.get("SITE_URL", "http://localhost:5173").rstrip("/")
    urls = [_url(site, chemin) for chemin in PAGES_FIXES]
    urls += [_url(site, f"/boutique/{u.value}") for u in Univers]
    for p in db.query(Produit).filter(Produit.visible.is_(True)).order_by(Produit.id):
        urls.append(_url(site, f"/produits/{p.id}"))
    actus = db.query(Actualite).filter(Actualite.publiee.is_(True)).order_by(Actualite.date_publication.desc())
    for a in actus:
        urls.append(_url(site, f"/actualites/{a.slug}", a.date_publication.date().isoformat()))
    corps = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(urls)
        + "</urlset>"
    )
    return Response(content=corps, media_type="application/xml")
