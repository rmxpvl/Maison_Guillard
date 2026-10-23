import enum
from decimal import Decimal

from sqlalchemy import Column, DateTime, Enum as SqlEnum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class StatutCommande(str, enum.Enum):
    en_attente = "en_attente"
    confirmee = "confirmee"
    expediee = "expediee"
    livree = "livree"
    annulee = "annulee"


class Commande(Base):
    __tablename__ = "commande"

    id = Column(Integer, primary_key=True, index=True)
    nom_client = Column(String, nullable=False)
    email = Column(String, nullable=False)
    telephone = Column(String, nullable=True)
    adresse = Column(String, nullable=False)
    statut = Column(
        SqlEnum(StatutCommande, name="statut_commande_enum"),
        nullable=False,
        default=StatutCommande.en_attente,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    lignes = relationship(
        "LigneCommande",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # Not a column: recomputed from the lines each time it is read.
    @property
    def total(self) -> Decimal:
        return sum(
            (ligne.prix_unitaire_snapshot * ligne.quantite for ligne in self.lignes),
            Decimal("0"),
        )


class LigneCommande(Base):
    __tablename__ = "ligne_commande"

    id = Column(Integer, primary_key=True, index=True)
    commande_id = Column(
        Integer, ForeignKey("commande.id", ondelete="CASCADE"), nullable=False
    )
    # No cascade here: deleting a produit must never erase an order line.
    produit_id = Column(Integer, ForeignKey("produit.id"), nullable=False)
    quantite = Column(Integer, nullable=False)
    prix_unitaire_snapshot = Column(Numeric(10, 2), nullable=False)
    produit = relationship("Produit", lazy="selectin")
