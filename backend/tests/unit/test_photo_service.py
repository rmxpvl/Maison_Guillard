import io
from unittest.mock import MagicMock

from fastapi import UploadFile

from app.services import photo_service


def test_upload_to_cloudinary_saves_file_and_returns_local_url(tmp_path, monkeypatch):
    monkeypatch.setattr(photo_service, "UPLOAD_DIR", tmp_path)
    fichier = UploadFile(filename="chaise.jpg", file=io.BytesIO(b"fake-image-bytes"))

    url = photo_service.upload_to_cloudinary(fichier)

    assert url.startswith("http://localhost:")
    assert "/uploads/" in url
    saved_files = list(tmp_path.iterdir())
    assert len(saved_files) == 1
    assert saved_files[0].read_bytes() == b"fake-image-bytes"


def test_attach_to_produit_creates_a_photo():
    db = MagicMock()

    photo = photo_service.attach_to_produit(db, produit_id=1, url="http://x/y.jpg", ordre=2)

    assert photo.produit_id == 1
    assert photo.url == "http://x/y.jpg"
    assert photo.ordre == 2
    assert photo.principale is False
    db.add.assert_called_once()
    db.commit.assert_called_once()


def test_delete_returns_false_when_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    result = photo_service.delete(db, 999)

    assert result is False


def test_delete_returns_true_when_found():
    db = MagicMock()
    photo = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = photo

    result = photo_service.delete(db, 1)

    assert result is True
    db.delete.assert_called_once_with(photo)


def test_set_principale_returns_none_when_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    result = photo_service.set_principale(db, 999)

    assert result is None


def test_set_principale_unsets_other_photos_for_same_produit():
    db = MagicMock()
    photo = MagicMock(id=5, produit_id=1)
    db.query.return_value.filter.return_value.first.return_value = photo

    result = photo_service.set_principale(db, 5)

    assert result is photo
    assert photo.principale is True
    # the bulk-unset query ran against the same produit_id
    update_call = db.query.return_value.filter.return_value.update
    update_call.assert_called_once_with({"principale": False}, synchronize_session=False)
    db.commit.assert_called_once()


# ---------- file checks and Cloudinary ----------
import hashlib  # noqa: E402
from unittest.mock import patch  # noqa: E402

import httpx  # noqa: E402
import pytest  # noqa: E402


def _fichier(nom="chaise.jpg", contenu=b"octets-image", type_contenu=None):
    return UploadFile(filename=nom, file=io.BytesIO(contenu), headers={"content-type": type_contenu} if type_contenu else None)


@pytest.mark.parametrize("nom", ["virus.exe", "page.html", "dessin.svg", "sans-extension", "double.jpg.php", ""])
def test_refuse_un_fichier_qui_n_est_pas_une_image(tmp_path, monkeypatch, nom):
    monkeypatch.setattr(photo_service, "UPLOAD_DIR", tmp_path)

    with pytest.raises(photo_service.ImageInvalideError, match="Format non accepté"):
        photo_service.upload_to_cloudinary(_fichier(nom))

    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("nom", ["a.jpg", "a.JPEG", "a.png", "a.webp", "a.gif"])
def test_accepte_les_formats_d_image_courants(tmp_path, monkeypatch, nom):
    monkeypatch.setattr(photo_service, "UPLOAD_DIR", tmp_path)

    assert photo_service.upload_to_cloudinary(_fichier(nom)).startswith("http")


def test_refuse_un_type_de_contenu_qui_n_est_pas_une_image(tmp_path, monkeypatch):
    monkeypatch.setattr(photo_service, "UPLOAD_DIR", tmp_path)

    with pytest.raises(photo_service.ImageInvalideError):
        photo_service.upload_to_cloudinary(_fichier("a.jpg", type_contenu="text/html"))


def test_refuse_une_image_trop_lourde_ou_vide(tmp_path, monkeypatch):
    monkeypatch.setattr(photo_service, "UPLOAD_DIR", tmp_path)

    with pytest.raises(photo_service.ImageInvalideError, match="trop lourde"):
        photo_service.upload_to_cloudinary(_fichier("a.jpg", b"x" * (photo_service.TAILLE_MAX + 1)))
    with pytest.raises(photo_service.ImageInvalideError, match="vide"):
        photo_service.upload_to_cloudinary(_fichier("a.jpg", b""))


def test_le_nom_envoye_n_est_jamais_utilise_pour_le_fichier_stocke(tmp_path, monkeypatch):
    monkeypatch.setattr(photo_service, "UPLOAD_DIR", tmp_path)

    photo_service.upload_to_cloudinary(_fichier("../../etc/passwd.png"))

    (enregistre,) = list(tmp_path.iterdir())
    assert enregistre.parent == tmp_path and enregistre.suffix == ".png" and "passwd" not in enregistre.name


@pytest.fixture
def cloudinary(monkeypatch):
    monkeypatch.setenv("CLOUDINARY_URL", "cloudinary://123456:secret-abc@mon-atelier")


def test_envoie_l_image_a_cloudinary_avec_une_signature_valide(cloudinary):
    reponse = httpx.Response(200, json={"secure_url": "https://res.cloudinary.com/mon-atelier/image/upload/v1/maison-guillard/x.jpg"})
    with patch("app.services.photo_service.httpx.post", return_value=reponse) as post, \
         patch("app.services.photo_service.time.time", return_value=1700000000):
        url = photo_service.upload_to_cloudinary(_fichier("chaise.jpg", b"octets"))

    assert url == "https://res.cloudinary.com/mon-atelier/image/upload/v1/maison-guillard/x.jpg"
    (adresse,), kwargs = post.call_args
    assert adresse == "https://api.cloudinary.com/v1_1/mon-atelier/image/upload"
    assert kwargs["data"]["api_key"] == "123456" and kwargs["data"]["folder"] == "maison-guillard"
    attendue = hashlib.sha1(b"folder=maison-guillard&timestamp=1700000000secret-abc").hexdigest()
    assert kwargs["data"]["signature"] == attendue
    assert "secret-abc" not in str(kwargs["data"])  # the secret signs, it is never sent
    assert kwargs["files"]["file"][1] == b"octets"


@pytest.mark.parametrize("panne", [
    {"side_effect": httpx.ConnectError("réseau coupé")},
    {"return_value": httpx.Response(401, json={"error": {"message": "Invalid Signature"}})},
    {"return_value": httpx.Response(200, json={})},
])
def test_une_panne_cloudinary_est_signalee_sans_rien_enregistrer(cloudinary, tmp_path, monkeypatch, panne):
    monkeypatch.setattr(photo_service, "UPLOAD_DIR", tmp_path)
    with patch("app.services.photo_service.httpx.post", **panne):
        with pytest.raises(photo_service.StockageIndisponibleError):
            photo_service.upload_to_cloudinary(_fichier())

    assert list(tmp_path.iterdir()) == []


def test_sans_cloudinary_le_disque_local_sert_au_developpement(monkeypatch, tmp_path):
    monkeypatch.delenv("CLOUDINARY_URL", raising=False)
    monkeypatch.setattr(photo_service, "UPLOAD_DIR", tmp_path)

    assert "/uploads/" in photo_service.upload_to_cloudinary(_fichier())
