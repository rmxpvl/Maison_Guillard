from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ActualiteIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    titre: str = Field(min_length=1, max_length=150)
    contenu: str = Field(min_length=1, max_length=20000)
    publiee: bool = False
    date_publication: Optional[datetime] = None


class ActualiteUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    titre: Optional[str] = Field(default=None, min_length=1, max_length=150)
    contenu: Optional[str] = Field(default=None, min_length=1, max_length=20000)
    publiee: Optional[bool] = None
    date_publication: Optional[datetime] = None


class LegendeIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    legende: Optional[str] = Field(default=None, max_length=200)


class PhotoActualiteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    legende: Optional[str]
    ordre: int


class ActualiteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titre: str
    slug: str
    contenu: str
    publiee: bool
    date_publication: datetime
    photos: list[PhotoActualiteOut]
