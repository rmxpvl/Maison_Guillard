from sqlalchemy import Column, Integer, Numeric, String, Text

from app.database import Base

COND_PAIEMENT = (
    "Le devis est payable en totalité en ligne, après son acceptation, et jusqu'à sa date d'expiration."
)
COND_FABRICATION = "Fabrication et livraison garanties sous 15 jours après le paiement, sauf cas extrême."
COND_ANNULATION = (
    "Avant le paiement, vous pouvez refuser le devis. Après le paiement et avant le début de la "
    "fabrication, l'annulation donne lieu à un remboursement total. Une fois la fabrication "
    "commencée, contactez l'atelier : l'artisane décide au cas par cas."
)


# Quote settings the artisane edits. A single row, created on first read.
class Parametre(Base):
    __tablename__ = "parametre"

    id = Column(Integer, primary_key=True)

    # Company identity, printed on every quote
    nom_commercial = Column(String, nullable=False, default="Maison Guillard")
    nom_legal = Column(String, nullable=False, default="")
    adresse = Column(String, nullable=False, default="")
    siret = Column(String, nullable=False, default="")
    email = Column(String, nullable=False, default="")
    telephone = Column(String, nullable=False, default="")
    prenom_signature = Column(String, nullable=False, default="")
    mention_tva = Column(String, nullable=False, default="")

    validite_jours = Column(Integer, nullable=False, default=30)
    # Default delivery fees, one per univers
    frais_meubles = Column(Numeric(10, 2), nullable=False, default=0)
    frais_ceramique = Column(Numeric(10, 2), nullable=False, default=0)
    frais_papeterie = Column(Numeric(10, 2), nullable=False, default=0)

    # Terms printed at the bottom of the quote
    cond_paiement = Column(Text, nullable=False, default=COND_PAIEMENT)
    cond_fabrication = Column(Text, nullable=False, default=COND_FABRICATION)
    cond_annulation = Column(Text, nullable=False, default=COND_ANNULATION)
