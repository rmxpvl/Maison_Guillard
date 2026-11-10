from sqlalchemy import Boolean, Column, Integer, String, Numeric, ForeignKey, DateTime
from sqlalchemy.sql import func, true
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.teinte import produit_teinte


class Produit(Base):
    __tablename__ = "produit"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    description = Column(String, nullable=False)
    categorie_id = Column(Integer, ForeignKey("categorie.id"), nullable=False)
    prix = Column(Numeric(10, 2), nullable=False)
    dimensions = Column(String, nullable=False)
    visible = Column(Boolean, nullable=False, default=True, server_default=true())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    teintes = relationship(
        "Teinte",
        secondary=produit_teinte,
        order_by="Teinte.ordre",
        lazy="selectin",
    )
    photos = relationship(
        "Photo",
        order_by="Photo.ordre",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
