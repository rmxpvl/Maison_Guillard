import os
from collections.abc import Mapping

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Settings that depend on where the API runs. Locally nothing here is required; in production
# (APP_ENV=production) the API refuses to start with a missing or dangerous setting rather than
# run half configured.

PLACEHOLDER_JWT = "replace-with-a-long-random-string"


def normaliser_url_base(url: str) -> str:
    """Render hands out postgres://… ; SQLAlchemy needs to be told to use the psycopg driver."""
    for debut in ("postgres://", "postgresql://"):
        if url.startswith(debut):
            return "postgresql+psycopg://" + url[len(debut):]
    return url


def origines_autorisees(valeur: str | None) -> list[str]:
    """CORS_ORIGINS="https://a.fr, https://b.fr" -> the list of origins allowed to call the API."""
    return [o.strip().rstrip("/") for o in (valeur or "").split(",") if o.strip()]


def configurer_cors(app: FastAPI, origines: list[str]) -> None:
    """The site calls the API from its own domain. Only those origins are allowed, with the
    bearer token header; no cookie is ever shared (credentials stay off)."""
    if not origines:
        return
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origines,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        allow_credentials=False,
    )


def en_production(env: Mapping[str, str] = os.environ) -> bool:
    return env.get("APP_ENV") == "production"


def documentation_ouverte(env: Mapping[str, str] = os.environ) -> bool:
    """Swagger (/docs) is closed in production unless DOCS_ENABLED=1: no need to list the admin routes."""
    return not en_production(env) or env.get("DOCS_ENABLED") == "1"


def problemes_production(env: Mapping[str, str] = os.environ) -> list[str]:
    if not en_production(env):
        return []
    problemes = []

    secret = env.get("JWT_SECRET", "")
    if len(secret) < 32 or secret.startswith(PLACEHOLDER_JWT):
        problemes.append("JWT_SECRET : une valeur aléatoire d'au moins 32 caractères est obligatoire")
    if not env.get("STRIPE_SECRET_KEY", "").startswith("sk_"):
        problemes.append("STRIPE_SECRET_KEY : clé secrète Stripe manquante (elle commence par sk_)")
    if not env.get("STRIPE_WEBHOOK_SECRET", "").startswith("whsec_"):
        problemes.append("STRIPE_WEBHOOK_SECRET : secret du webhook Stripe manquant (il commence par whsec_)")
    if not env.get("SITE_URL", "").startswith("https://"):
        problemes.append("SITE_URL : l'adresse publique du site en https:// est obligatoire (liens des e-mails et retour de Stripe)")
    origines = origines_autorisees(env.get("CORS_ORIGINS"))
    if not origines or not all(o.startswith("https://") for o in origines):
        problemes.append("CORS_ORIGINS : au moins une origine en https:// est obligatoire (le site)")
    if not env.get("CLOUDINARY_URL", "").startswith("cloudinary://"):
        problemes.append("CLOUDINARY_URL : sans elle les photos seraient perdues à chaque déploiement")
    for variable in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "EMAIL_EXPEDITEUR", "EMAIL_ARTISAN"):
        if not env.get(variable):
            problemes.append(f"{variable} : réglage d'envoi des e-mails manquant")
    return problemes


def verifier_production(env: Mapping[str, str] = os.environ) -> None:
    problemes = problemes_production(env)
    if problemes:
        raise RuntimeError(
            "Configuration de production incomplète ou dangereuse :\n- " + "\n- ".join(problemes)
        )
