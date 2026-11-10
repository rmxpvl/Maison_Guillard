import enum

from sqlalchemy import Column, DateTime, Enum as SqlEnum, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class TypeJeton(str, enum.Enum):
    activation = "activation"  # first e-mail link: proves the mailbox, then the password is chosen
    reinitialisation = "reinitialisation"


class Client(Base):
    __tablename__ = "client"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)  # stored lowercase
    # None until the customer has followed the activation link and chosen a password.
    password_hash = Column(String, nullable=True)
    email_verifie_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JetonClient(Base):
    """Single-use link token (activation, password reset). Only its hash is stored."""

    __tablename__ = "jeton_client"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("client.id", ondelete="CASCADE"), nullable=False)
    type = Column(SqlEnum(TypeJeton, name="type_jeton_enum"), nullable=False)
    token_hash = Column(String, unique=True, nullable=False, index=True)
    expire_at = Column(DateTime(timezone=True), nullable=False)
    utilise_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
