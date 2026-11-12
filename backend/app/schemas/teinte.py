from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TeinteUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nom: Optional[str] = Field(default=None, min_length=1, max_length=40)
    ordre: Optional[int] = Field(default=None, ge=0)
    active: Optional[bool] = None


class TeinteOut(BaseModel):
    id: int
    nom: str
    image_url: str
    ordre: int
    active: bool

    model_config = ConfigDict(from_attributes=True)
