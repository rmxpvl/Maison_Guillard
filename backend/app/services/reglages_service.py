from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.message_type import MessageType
from app.models.parametre import Parametre

CHAMPS = (
    "nom_commercial", "nom_legal", "adresse", "siret", "email", "telephone", "prenom_signature",
    "mention_tva", "validite_jours", "frais_meubles", "frais_ceramique", "frais_papeterie",
    "cond_paiement", "cond_fabrication", "cond_annulation",
)
# Needed to send a quote (spec 5.7), in the order shown to the artisane.
OBLIGATOIRES = (("nom_legal", "nom légal"), ("adresse", "adresse"), ("siret", "SIRET"), ("email", "e-mail"))


def get(db: Session) -> Parametre:
    parametre = db.query(Parametre).first()
    if parametre is None:
        parametre = Parametre(id=1)
        db.add(parametre)
        db.commit()
        db.refresh(parametre)
    return parametre


def update(db: Session, data: dict) -> Parametre:
    parametre = get(db)
    for champ in CHAMPS:
        setattr(parametre, champ, data[champ])
    db.commit()
    db.refresh(parametre)
    return parametre


def champs_manquants(parametre) -> list[str]:
    return [libelle for champ, libelle in OBLIGATOIRES if not (getattr(parametre, champ) or "").strip()]


def frais_par_defaut(univers: list[str], parametre) -> Decimal:
    """Default delivery fee of a request. Provisional rule (to review with the artisane): when it
    mixes several univers, take the highest fee. Kept in this single function."""
    frais = [getattr(parametre, f"frais_{u}") for u in univers]
    return max(frais, default=Decimal("0"))


def snapshot(parametre) -> dict:
    """What a quote prints and the settings could change later: frozen with the quote."""
    return {
        "entreprise": {
            champ: getattr(parametre, champ)
            for champ in ("nom_commercial", "nom_legal", "adresse", "siret", "email", "telephone",
                          "prenom_signature", "mention_tva")
        },
        "conditions": {
            "paiement": parametre.cond_paiement,
            "fabrication": parametre.cond_fabrication,
            "annulation": parametre.cond_annulation,
        },
    }


def messages_types(db: Session) -> list[MessageType]:
    return db.query(MessageType).order_by(MessageType.ordre, MessageType.id).all()


def creer_message_type(db: Session, data: dict) -> MessageType:
    dernier = max((m.ordre for m in messages_types(db)), default=-1)
    message = MessageType(**data, ordre=dernier + 1)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def modifier_message_type(db: Session, message_id: int, data: dict) -> MessageType | None:
    message = db.query(MessageType).filter(MessageType.id == message_id).first()
    if message is None:
        return None
    message.titre, message.texte = data["titre"], data["texte"]
    db.commit()
    db.refresh(message)
    return message


def supprimer_message_type(db: Session, message_id: int) -> bool:
    message = db.query(MessageType).filter(MessageType.id == message_id).first()
    if message is None:
        return False
    db.delete(message)
    db.commit()
    return True
