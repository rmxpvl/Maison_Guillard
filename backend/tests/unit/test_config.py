import pytest

from app import config

PROD = {
    "APP_ENV": "production",
    "JWT_SECRET": "x" * 48,
    "STRIPE_SECRET_KEY": "sk_live_abc",
    "STRIPE_WEBHOOK_SECRET": "whsec_abc",
    "SITE_URL": "https://maisonguillard.fr",
    "CORS_ORIGINS": "https://maisonguillard.fr",
    "CLOUDINARY_URL": "cloudinary://1:secret@atelier",
    "SMTP_HOST": "smtp-relay.brevo.com",
    "SMTP_PORT": "587",
    "SMTP_USER": "user",
    "SMTP_PASSWORD": "pass",
    "EMAIL_EXPEDITEUR": "Maison Guillard <contact@maisonguillard.fr>",
    "EMAIL_ARTISAN": "atelier@maisonguillard.fr",
}


@pytest.mark.parametrize("fournie, attendue", [
    ("postgres://u:p@h:5432/db", "postgresql+psycopg://u:p@h:5432/db"),
    ("postgresql://u:p@h/db", "postgresql+psycopg://u:p@h/db"),
    ("postgresql+psycopg://u:p@h/db", "postgresql+psycopg://u:p@h/db"),
])
def test_l_adresse_de_base_fournie_par_render_est_adaptee_au_pilote_psycopg(fournie, attendue):
    assert config.normaliser_url_base(fournie) == attendue


def test_origines_cors_lues_depuis_une_liste_separee_par_des_virgules():
    assert config.origines_autorisees(" https://a.fr/ , https://b.fr,, ") == ["https://a.fr", "https://b.fr"]
    assert config.origines_autorisees("") == []
    assert config.origines_autorisees(None) == []


def test_hors_production_aucun_controle_n_est_exige():
    assert config.en_production({}) is False
    assert config.problemes_production({"JWT_SECRET": "court"}) == []


def test_une_configuration_de_production_complete_ne_pose_aucun_probleme():
    assert config.en_production(PROD) is True
    assert config.problemes_production(PROD) == []


@pytest.mark.parametrize("variable, valeur, attendu", [
    ("JWT_SECRET", "court", "JWT_SECRET"),
    ("JWT_SECRET", "replace-with-a-long-random-string-" + "x" * 20, "JWT_SECRET"),
    ("JWT_SECRET", None, "JWT_SECRET"),
    ("STRIPE_SECRET_KEY", None, "STRIPE_SECRET_KEY"),
    ("STRIPE_SECRET_KEY", "pas-une-cle", "STRIPE_SECRET_KEY"),
    ("STRIPE_WEBHOOK_SECRET", "autre", "STRIPE_WEBHOOK_SECRET"),
    ("SITE_URL", "http://localhost:5173", "SITE_URL"),
    ("CORS_ORIGINS", None, "CORS_ORIGINS"),
    ("CORS_ORIGINS", "http://insecure.fr", "CORS_ORIGINS"),
    ("CLOUDINARY_URL", None, "CLOUDINARY_URL"),
    ("SMTP_PASSWORD", None, "SMTP_PASSWORD"),
    ("EMAIL_ARTISAN", None, "EMAIL_ARTISAN"),
])
def test_chaque_reglage_dangereux_ou_manquant_est_signale_en_production(variable, valeur, attendu):
    env = {**PROD}
    if valeur is None:
        env.pop(variable)
    else:
        env[variable] = valeur

    problemes = config.problemes_production(env)

    assert len(problemes) == 1 and attendu in problemes[0]


def test_le_demarrage_est_refuse_avec_la_liste_de_tout_ce_qui_manque():
    with pytest.raises(RuntimeError) as erreur:
        config.verifier_production({"APP_ENV": "production"})

    message = str(erreur.value)
    assert "JWT_SECRET" in message and "STRIPE_SECRET_KEY" in message and "CLOUDINARY_URL" in message


def test_la_documentation_de_l_api_est_fermee_en_production_sauf_demande():
    assert config.documentation_ouverte({}) is True
    assert config.documentation_ouverte(PROD) is False
    assert config.documentation_ouverte({**PROD, "DOCS_ENABLED": "1"}) is True
