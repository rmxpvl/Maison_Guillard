from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.demande import Demande
from app.models.message_demande import AuteurMessage, MessageDemande


def lister(db: Session, demande: Demande, lecteur: AuteurMessage) -> list[MessageDemande]:
    """The thread, oldest first. Reading it marks the other side's messages as read."""
    db.query(MessageDemande).filter(
        MessageDemande.demande_id == demande.id,
        MessageDemande.auteur != lecteur,
        MessageDemande.lu_at.is_(None),
    ).update({"lu_at": datetime.now(timezone.utc)})
    db.commit()
    return (
        db.query(MessageDemande)
        .filter(MessageDemande.demande_id == demande.id)
        .order_by(MessageDemande.id)
        .all()
    )


def poster(db: Session, demande: Demande, auteur: AuteurMessage, texte: str) -> MessageDemande:
    message = MessageDemande(demande_id=demande.id, auteur=auteur, texte=texte)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def non_lus(db: Session, demande_ids: list[int], pour: AuteurMessage) -> dict[int, int]:
    """Messages written by the other side and not opened yet, per demande."""
    if not demande_ids:
        return {}
    lignes = (
        db.query(MessageDemande.demande_id, func.count())
        .filter(
            MessageDemande.demande_id.in_(demande_ids),
            MessageDemande.auteur != pour,
            MessageDemande.lu_at.is_(None),
        )
        .group_by(MessageDemande.demande_id)
        .all()
    )
    return dict(lignes)
