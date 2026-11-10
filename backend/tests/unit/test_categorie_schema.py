import pytest
from pydantic import ValidationError

from app.schemas.categorie import CategorieCreate


@pytest.mark.parametrize("slug", ["Test", "test qa", "té", ""])
def test_categorie_create_refuse_un_slug_invalide(slug):
    with pytest.raises(ValidationError):
        CategorieCreate(nom="Test", slug=slug, univers="meubles")


def test_categorie_create_accepte_un_slug_valide():
    assert CategorieCreate(nom="Bols", slug="bols-2", univers="meubles").slug == "bols-2"
