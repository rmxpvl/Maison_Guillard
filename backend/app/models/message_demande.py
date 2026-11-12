import enum

from sqlalchemy import Column, DateTime, Enum as SqlEnum, ForeignKey, Integer, Text
from sqlalchemy.sql import func

from app.database import Base


class AuteurMessage(str, enum.Enum):
    client = "client"
    artisane = "artisane"


class MessageDemande(Base):
    """One message of the discussion thread of a demande, between the customer and the artisane."""

    __tablename__ = "message_demande"

    id = Column(Integer, primary_key=True, index=True)
    demande_id = Column(Integer, ForeignKey("demande.id", ondelete="CASCADE"), nullable=False, index=True)
    auteur = Column(SqlEnum(AuteurMessage, name="auteur_message_enum"), nullable=False)
    texte = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Set when the other side has opened the thread (unread counters).
    lu_at = Column(DateTime(timezone=True), nullable=True)
