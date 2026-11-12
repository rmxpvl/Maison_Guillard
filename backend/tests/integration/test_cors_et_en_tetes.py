from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import config
from app.main import app

client = TestClient(app)


def test_les_reponses_de_l_api_interdisent_le_reniflage_de_type():
    res = client.get("/api/health")

    assert res.headers["x-content-type-options"] == "nosniff"
    assert res.headers["referrer-policy"] == "no-referrer"


def test_par_defaut_aucune_origine_n_est_autorisee():
    res = client.get("/api/health", headers={"Origin": "https://autre-site.fr"})

    assert "access-control-allow-origin" not in res.headers


def _petite_api(origines):
    petite = FastAPI()
    config.configurer_cors(petite, origines)

    @petite.get("/ping")
    def ping():
        return {"ok": True}

    return TestClient(petite)


def test_une_origine_autorisee_peut_appeler_l_api_et_envoyer_le_jeton():
    c = _petite_api(["https://maisonguillard.fr"])

    pre = c.options("/ping", headers={
        "Origin": "https://maisonguillard.fr",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type",
    })
    reponse = c.get("/ping", headers={"Origin": "https://maisonguillard.fr"})

    assert pre.status_code == 200
    assert pre.headers["access-control-allow-origin"] == "https://maisonguillard.fr"
    assert "authorization" in pre.headers["access-control-allow-headers"].lower()
    assert reponse.headers["access-control-allow-origin"] == "https://maisonguillard.fr"


def test_une_autre_origine_est_refusee_et_les_cookies_ne_sont_pas_partages():
    c = _petite_api(["https://maisonguillard.fr"])

    reponse = c.get("/ping", headers={"Origin": "https://pirate.fr"})
    autorisee = c.get("/ping", headers={"Origin": "https://maisonguillard.fr"})

    assert "access-control-allow-origin" not in reponse.headers
    assert "access-control-allow-credentials" not in autorisee.headers  # the app uses a bearer token, no cookie


def test_sans_origine_configuree_aucun_en_tete_cors():
    c = _petite_api([])

    assert "access-control-allow-origin" not in c.get("/ping", headers={"Origin": "https://x.fr"}).headers
