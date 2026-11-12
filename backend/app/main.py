import os

from fastapi import Depends, FastAPI, Request

from app import config
from app.dependencies.require_admin import require_admin
from fastapi.staticfiles import StaticFiles

from app.routers import actualites, auth, categories, clients, contenus, demandes, informations, produits, reglages, stripe_webhook, teintes
from app.routers.reponses import NON_AUTORISE
from app.services.photo_service import UPLOAD_DIR

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# In production: refuse to start with a missing or dangerous setting (see app/config.py).
config.verifier_production()

DESCRIPTION = """
API de **Maison Guillard**, mobilier artisanal en bois massif.

- Les routes de **lecture** (catalogue) sont publiques.
- Les routes d'**écriture** (🔒) sont réservées à l'administrateur :
  1. appelez `POST /api/auth/login` avec l'e-mail et le mot de passe admin ;
  2. copiez le `token` reçu ;
  3. cliquez sur **Authorize** en haut de la page et collez-le.
"""

TAGS = [
    {"name": "Authentification", "description": "Connexion de l'administrateur."},
    {"name": "Catégories", "description": "Familles de produits : tables, chaises, tabourets, lampes."},
    {"name": "Produits", "description": "Catalogue : consultation publique, gestion réservée à l'admin."},
    {"name": "Teintes", "description": "Finitions proposées sur les produits : gestion réservée à l'admin."},
    {"name": "Photos", "description": "Photos d'un produit : photo principale, suppression."},
    {"name": "Réglages du devis", "description": "Identité de l'entreprise, validité, frais de livraison, conditions et messages types."},
    {"name": "Comptes clients", "description": "Inscription par lien e-mail, connexion, mot de passe oublié, mes demandes."},
    {"name": "Informations légales", "description": "Identité de l'entreprise pour les mentions légales."},
    {"name": "Actualités", "description": "Les nouvelles de l'atelier : lecture publique, écriture réservée à l'admin."},
    {"name": "Contenus du site", "description": "Textes et photos des pages publiques, modifiables par l'artisane."},
    {"name": "Paiement", "description": "Webhook Stripe : confirmation des paiements."},
    {"name": "Demandes", "description": "Ma demande : pièces du catalogue ou projet libre, puis devis de l'artisane."},
    {"name": "Santé", "description": "Vérifier que l'API répond."},
]

app = FastAPI(
    title="Maison Guillard API",
    version="1.0.0",
    description=DESCRIPTION,
    openapi_tags=TAGS,
    docs_url="/docs" if config.documentation_ouverte() else None,
    redoc_url="/redoc" if config.documentation_ouverte() else None,
    openapi_url="/openapi.json" if config.documentation_ouverte() else None,
)

config.configurer_cors(app, config.origines_autorisees(os.environ.get("CORS_ORIGINS")))


@app.middleware("http")
async def en_tetes_de_securite(requete: Request, suite):
    reponse = await suite(requete)
    reponse.headers["X-Content-Type-Options"] = "nosniff"
    reponse.headers["Referrer-Policy"] = "no-referrer"
    return reponse


app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(produits.router)
app.include_router(produits.photos_router)
app.include_router(teintes.router)
app.include_router(clients.router)
app.include_router(demandes.router)
app.include_router(reglages.router)
app.include_router(actualites.router)
app.include_router(contenus.router)
app.include_router(informations.router)
app.include_router(stripe_webhook.router)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


@app.get("/api/health", tags=["Santé"], summary="Vérifier que l'API répond")
def health_check():
    return {"status": "ok"}


# Exercises require_admin end-to-end; also useful during S5+ manual testing.
@app.get(
    "/api/health/protected-check",
    tags=["Santé"],
    summary="Vérifier un jeton administrateur",
    responses=NON_AUTORISE,
)
def protected_health_check(admin: dict = Depends(require_admin)):
    return {"status": "ok", "admin": admin["email"]}
