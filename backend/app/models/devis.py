import enum

from sqlalchemy import Column, DateTime, Enum as SqlEnum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class StatutDevis(str, enum.Enum):
    nouveau = "nouveau"
    en_discussion = "en_discussion"
    accepte = "accepte"
    refuse = "refuse"


class Devis(Base):
    __tablename__ = "devis"

    id = Column(Integer, primary_key=True, index=True)
    nom_client = Column(String, nullable=False)
    email = Column(String, nullable=False)
    telephone = Column(String, nullable=True)
    # SET NULL: deleting the produit keeps the quote, only the link is lost.
    produit_id = Column(Integer, ForeignKey("produit.id", ondelete="SET NULL"), nullable=True)
    description_projet = Column(String, nullable=False)
    statut = Column(
        SqlEnum(StatutDevis, name="statut_devis_enum"),
        nullable=False,
        default=StatutDevis.nouveau,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    produit = relationship("Produit", lazy="selectin")
    @property
    def nom_produit(self) -> str | None:
        return self.produit.nom if self.produit else None
    
