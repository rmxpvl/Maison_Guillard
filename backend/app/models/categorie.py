import enum

from sqlalchemy import Column, Integer, String
from sqlalchemy import Enum as SqlEnum

from app.database import Base


class Univers(str, enum.Enum):
    meubles = "meubles"
    ceramique = "ceramique"
    papeterie = "papeterie"


class Categorie(Base):
    __tablename__ = "categorie"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)
    univers = Column(SqlEnum(Univers, name="univers_enum"), nullable=False)
