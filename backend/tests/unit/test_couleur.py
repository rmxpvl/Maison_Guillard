from PIL import Image

from app.services import couleur


def test_couleur_d_un_svg_uni(tmp_path, monkeypatch):
    monkeypatch.setattr(couleur, "UPLOAD_DIR", tmp_path)
    (tmp_path / "t.svg").write_text('<svg><rect width="1" height="1" fill="#3b3836"/></svg>', encoding="utf-8")

    assert couleur.couleur_depuis_url("http://localhost:3000/uploads/t.svg") == "#3b3836"


def test_couleur_moyenne_d_une_image(tmp_path, monkeypatch):
    monkeypatch.setattr(couleur, "UPLOAD_DIR", tmp_path)
    Image.new("RGB", (8, 8), (138, 103, 71)).save(tmp_path / "t.png")

    assert couleur.couleur_depuis_url("https://site.test/uploads/t.png") == "#8a6747"


def test_couleur_inconnue_pour_une_image_distante_absente_ou_illisible(tmp_path, monkeypatch):
    monkeypatch.setattr(couleur, "UPLOAD_DIR", tmp_path)
    (tmp_path / "casse.png").write_bytes(b"pas une image")

    assert couleur.couleur_depuis_url("https://res.cloudinary.com/x/teinte.jpg") is None
    assert couleur.couleur_depuis_url("http://localhost:3000/uploads/absente.png") is None
    assert couleur.couleur_depuis_url("http://localhost:3000/uploads/casse.png") is None
    assert couleur.couleur_depuis_url("http://localhost:3000/uploads/../secret.png") is None
