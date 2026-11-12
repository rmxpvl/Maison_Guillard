from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Actualite(Base):
    """A news post of the workshop, written by the artisane in the back-office."""

    __tablename__ = "actualite"

    id = Column(Integer, primary_key=True, index=True)
    titre = Column(String, nullable=False)
    # Address of the post (/actualites/<slug>): made once from the title, then never changed so
    # that a shared link keeps working when the title is corrected.
    slug = Column(String, unique=True, nullable=False, index=True)
    contenu = Column(Text, nullable=False)  # plain text: blank line = new paragraph
    publiee = Column(Boolean, nullable=False, default=False, server_default="false")
    date_publication = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    photos = relationship(
        "PhotoActualite",
        order_by="PhotoActualite.ordre, PhotoActualite.id",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class PhotoActualite(Base):
    __tablename__ = "photo_actualite"

    id = Column(Integer, primary_key=True, index=True)
    actualite_id = Column(Integer, ForeignKey("actualite.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(String, nullable=False)
    legende = Column(String, nullable=True)
    ordre = Column(Integer, nullable=False, default=0, server_default="0")  # lowest = cover
