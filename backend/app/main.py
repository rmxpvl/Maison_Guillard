from fastapi import Depends, FastAPI

from app.dependencies.require_admin import require_admin
from fastapi.staticfiles import StaticFiles

from app.routers import auth, devis, categories, commandes, produits, parametres
from app.routers.reponses import NON_AUTORISE
from app.services.photo_service import UPLOAD_DIR

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

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
    {"name": "Photos", "description": "Photos d'un produit : photo principale, suppression."},
    {"name": "Commandes", "description": "Achat direct : un visiteur passe une commande."},
    {"name": "Devis", "description": "Demande de devis : projet sur mesure ou modèle à adapter."},
    {"name": "Paramètres", "description": "Réglages du site, dont l'e-mail automatique à chaque commande."},
    {"name": "Santé", "description": "Vérifier que l'API répond."},
]

app = FastAPI(
    title="Maison Guillard API",
    version="1.0.0",
    description=DESCRIPTION,
    openapi_tags=TAGS,
)

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(produits.router)
app.include_router(produits.photos_router)
app.include_router(commandes.router)
app.include_router(devis.router)
app.include_router(parametres.router)
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
