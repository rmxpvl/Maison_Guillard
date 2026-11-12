from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TexteIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    texte: Optional[str] = Field(default=None, max_length=5000)


class ContenuOut(BaseModel):
    cle: str
    texte: Optional[str]
    image_url: Optional[str]


class ContenuPublicOut(BaseModel):
    texte: Optional[str]
    image_url: Optional[str]
