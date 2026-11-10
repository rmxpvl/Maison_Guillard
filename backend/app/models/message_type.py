from sqlalchemy import Column, Integer, String, Text

from app.database import Base


# Reusable text the artisane inserts in a quote's message in one click.
class MessageType(Base):
    __tablename__ = "message_type"

    id = Column(Integer, primary_key=True, index=True)
    titre = Column(String, nullable=False)
    texte = Column(Text, nullable=False)
    ordre = Column(Integer, nullable=False, default=0, server_default="0")
