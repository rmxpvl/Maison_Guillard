from sqlalchemy import Column, Integer

from app.database import Base


# One counter per year: quote numbers are D-<year>-<counter>, with no gap and no duplicate.
class CompteurDevis(Base):
    __tablename__ = "compteur_devis"

    annee = Column(Integer, primary_key=True)
    dernier = Column(Integer, nullable=False)
