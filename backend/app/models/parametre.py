from sqlalchemy import Boolean, Column, Integer, false

from app.database import Base


# Site settings the admin can change. A single row, created on first read.
class Parametre(Base):
    __tablename__ = "parametre"

    id = Column(Integer, primary_key=True)
    email_commande_actif = Column(
        Boolean, nullable=False, default=False, server_default=false()
    )
