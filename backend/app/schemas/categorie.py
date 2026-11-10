from pydantic import BaseModel, ConfigDict, Field


class CategorieCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nom: str = Field(min_length=1, max_length=60)
    slug: str = Field(pattern=r"^[a-z0-9-]+$", max_length=60)


class CategorieOut(BaseModel):
    id: int
    nom: str
    slug: str

    model_config = ConfigDict(from_attributes=True)
