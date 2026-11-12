from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.sql import func

from app.database import Base


class ContenuSite(Base):
    """A text or a photo of a public page that the artisane changed. No row = the original one."""

    __tablename__ = "contenu_site"

    cle = Column(String, primary_key=True)  # e.g. "accueil.titre", see CLES in contenu_service
    texte = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
