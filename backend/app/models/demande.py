import enum
from decimal import Decimal

from sqlalchemy import JSON, Column, DateTime, Enum as SqlEnum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class StatutDemande(str, enum.Enum):
    nouvelle = "nouvelle"
    devis_envoye = "devis_envoye"
    payee = "payee"
    en_fabrication = "en_fabrication"
    expediee = "expediee"
    livree = "livree"
    refusee = "refusee"
    expiree = "expiree"
    annulee = "annulee"


class Demande(Base):
    __tablename__ = "demande"

    id = Column(Integer, primary_key=True, index=True)
    # Secret link of the customer's quote page: unguessable, never listed anywhere public.
    jeton = Column(String, unique=True, nullable=False, index=True)
    statut = Column(
        SqlEnum(StatutDemande, name="statut_demande_enum"),
        nullable=False,
        default=StatutDemande.nouvelle,
    )

    # Customer
    nom_client = Column(String, nullable=False)
    email = Column(String, nullable=False)
    telephone = Column(String, nullable=True)
    adresse = Column(String, nullable=True)  # a free project may not give it yet
    message_client = Column(String, nullable=True)
    description_projet = Column(String, nullable=True)
    produit_reference_id = Column(Integer, ForeignKey("produit.id", ondelete="SET NULL"), nullable=True)

    # Quote
    frais_livraison = Column(Numeric(10, 2), nullable=True)
    message_artisane = Column(String, nullable=True)
    numero_devis = Column(String, unique=True, nullable=True)
    version_devis = Column(Integer, nullable=False, default=1, server_default="1")
    devis_envoye_at = Column(DateTime(timezone=True), nullable=True)
    expire_at = Column(DateTime(timezone=True), nullable=True)
    # What the PDF shows and the settings could change later (company identity, VAT, terms).
    devis_snapshot = Column(JSON, nullable=True)
    cgv_acceptees_at = Column(DateTime(timezone=True), nullable=True)
    cgv_version = Column(String, nullable=True)

    # Payment
    stripe_session_id = Column(String, nullable=True)
    stripe_payment_intent_id = Column(String, nullable=True)
    montant_paye = Column(Numeric(10, 2), nullable=True)
    payee_at = Column(DateTime(timezone=True), nullable=True)
    date_limite = Column(DateTime(timezone=True), nullable=True)
    rembourse_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    lignes = relationship(
        "LigneDemande",
        order_by="LigneDemande.id",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    produit_reference = relationship("Produit", lazy="selectin")

    # Not a column: recomputed from the lines each time it is read.
    @property
    def total_final(self) -> Decimal | None:
        """Quoted total (final prices + delivery); None until a quote has been sent."""
        if self.numero_devis is None:
            return None
        lignes = sum(
            ((ligne.prix_final or Decimal("0")) * ligne.quantite for ligne in self.lignes), Decimal("0")
        )
        return lignes + (self.frais_livraison or Decimal("0"))

    @property
    def total_indicatif(self) -> Decimal:
        return sum(
            ((ligne.prix_indicatif or Decimal("0")) * ligne.quantite for ligne in self.lignes),
            Decimal("0"),
        )


class LigneDemande(Base):
    __tablename__ = "ligne_demande"

    id = Column(Integer, primary_key=True, index=True)
    demande_id = Column(Integer, ForeignKey("demande.id", ondelete="CASCADE"), nullable=False)
    # RESTRICT: a produit or teinte already requested is hidden / deactivated, never deleted.
    produit_id = Column(Integer, ForeignKey("produit.id", ondelete="RESTRICT"), nullable=True)
    libelle = Column(String, nullable=False)  # copy of the produit name, or a free line's text
    quantite = Column(Integer, nullable=False)
    teinte_id = Column(Integer, ForeignKey("teinte.id", ondelete="RESTRICT"), nullable=True)
    teinte_nom = Column(String, nullable=True)  # copy
    souhait = Column(String, nullable=True)
    prix_indicatif = Column(Numeric(10, 2), nullable=True)  # copy of the "from" price
    prix_final = Column(Numeric(10, 2), nullable=True)  # set by the artisane in the quote
