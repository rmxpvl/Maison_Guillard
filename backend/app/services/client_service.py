import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.client import Client, JetonClient, TypeJeton
from app.models.demande import Demande
from app.services import auth_service

DUREES = {TypeJeton.activation: timedelta(hours=48), TypeJeton.reinitialisation: timedelta(hours=1)}
JETON_CLIENT_HEURES = 24 * 7
# Checked when the account does not exist, so that "unknown address" and "wrong password" take
# the same time to answer.
_FAUX_HASH = auth_service.hash_password("faux-mot-de-passe-pour-egaliser-le-temps")


class LienInvalideError(Exception):
    """Activation / reset link unknown, already used or expired."""


def _empreinte(jeton: str) -> str:
    return hashlib.sha256(jeton.encode()).hexdigest()


def par_email(db: Session, email: str) -> Client | None:
    return db.query(Client).filter(Client.email == email).first()


def client_verifie(db: Session, email: str) -> Client | None:
    """The account that owns this address, if its owner has proved the mailbox."""
    client = db.query(Client).filter(Client.email == email.strip().lower()).first()
    return client if client and client.email_verifie_at else None


def _nouveau_lien(db: Session, client: Client, type_: TypeJeton) -> str:
    maintenant = datetime.now(timezone.utc)
    # Asking again cancels the previous link of the same kind.
    db.query(JetonClient).filter(
        JetonClient.client_id == client.id, JetonClient.type == type_, JetonClient.utilise_at.is_(None)
    ).update({"utilise_at": maintenant})
    brut = secrets.token_urlsafe(32)
    db.add(JetonClient(client_id=client.id, type=type_, token_hash=_empreinte(brut), expire_at=maintenant + DUREES[type_]))
    return brut


def _jeton_valide(db: Session, brut: str, type_: TypeJeton) -> JetonClient:
    jeton = (
        db.query(JetonClient)
        .filter(
            JetonClient.token_hash == _empreinte(brut),
            JetonClient.type == type_,
            JetonClient.utilise_at.is_(None),
            JetonClient.expire_at > datetime.now(timezone.utc),
        )
        .with_for_update()
        .first()
    )
    if jeton is None:
        raise LienInvalideError()
    return jeton


def demander_activation(db: Session, email: str) -> str | None:
    """Sign-up step 1: only the address is given. Returns the link token to e-mail, or None when
    the address already has an activated account (the caller then sends a reminder instead).
    The password is chosen AFTER the mailbox is proved, so nobody can pre-register an address
    that is not theirs with a password they know."""
    client = par_email(db, email)
    if client is None:
        client = Client(email=email)
        db.add(client)
        db.flush()
    elif client.email_verifie_at is not None and client.password_hash:
        return None
    brut = _nouveau_lien(db, client, TypeJeton.activation)
    db.commit()
    return brut


def rattacher_demandes(db: Session, client: Client) -> int:
    """Past requests sent with this address (and not yet in an account) join the account."""
    return (
        db.query(Demande)
        .filter(func.lower(Demande.email) == client.email, Demande.client_id.is_(None))
        .update({"client_id": client.id}, synchronize_session=False)
    )


def activer(db: Session, brut: str, mot_de_passe: str) -> Client:
    jeton = _jeton_valide(db, brut, TypeJeton.activation)
    client = db.get(Client, jeton.client_id)
    client.password_hash = auth_service.hash_password(mot_de_passe)
    client.email_verifie_at = client.email_verifie_at or datetime.now(timezone.utc)
    jeton.utilise_at = datetime.now(timezone.utc)
    rattacher_demandes(db, client)
    db.commit()
    db.refresh(client)
    return client


def mot_de_passe_oublie(db: Session, email: str) -> str | None:
    """Link token to e-mail, only for an activated account; None otherwise (nothing is revealed)."""
    client = par_email(db, email)
    if client is None or client.email_verifie_at is None or not client.password_hash:
        return None
    brut = _nouveau_lien(db, client, TypeJeton.reinitialisation)
    db.commit()
    return brut


def reinitialiser(db: Session, brut: str, mot_de_passe: str) -> Client:
    jeton = _jeton_valide(db, brut, TypeJeton.reinitialisation)
    client = db.get(Client, jeton.client_id)
    client.password_hash = auth_service.hash_password(mot_de_passe)
    jeton.utilise_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(client)
    return client


def connexion(db: Session, email: str, mot_de_passe: str) -> str:
    client = par_email(db, email)
    hash_ = client.password_hash if client and client.password_hash and client.email_verifie_at else None
    valide = auth_service.verify_password(mot_de_passe, hash_ or _FAUX_HASH)
    if client is None or hash_ is None or not valide:
        raise auth_service.InvalidCredentialsError()
    return auth_service.creer_jeton(client.id, client.email, "client", JETON_CLIENT_HEURES)


def supprimer(db: Session, client: Client, mot_de_passe: str) -> None:
    """The account goes; the requests stay (client_id becomes NULL): the workshop keeps its orders."""
    if not client.password_hash or not auth_service.verify_password(mot_de_passe, client.password_hash):
        raise auth_service.InvalidCredentialsError()
    db.delete(client)
    db.commit()


def demandes_du_client(db: Session, client: Client) -> list[Demande]:
    return db.query(Demande).filter(Demande.client_id == client.id).order_by(Demande.id.desc()).all()
