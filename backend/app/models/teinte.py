from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table
from sqlalchemy.sql import true

from app.database import Base

produit_teinte = Table(
    "produit_teinte",
    Base.metadata,
    Column("produit_id", Integer, ForeignKey("produit.id", ondelete="CASCADE"), primary_key=True),
    Column("teinte_id", Integer, ForeignKey("teinte.id", ondelete="RESTRICT"), primary_key=True),
)


class Teinte(Base):
    __tablename__ = "teinte"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    image_url = Column(String, nullable=False)
    ordre = Column(Integer, nullable=False, default=0, server_default="0")
    active = Column(Boolean, nullable=False, default=True, server_default=true())
