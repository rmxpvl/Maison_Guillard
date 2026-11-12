import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.require_client import require_client
from app.models.client import Client
from app.models.message_demande import AuteurMessage
from app.schemas.client import (
    ActivationIn,
    ConnexionIn,
    DemandeCompteOut,
    MessageGenerique,
    MoiOut,
    MotDePasseOublieIn,
    InscriptionIn,
    ReinitialisationIn,
    SupprimerCompteIn,
    TokenOut,
)
from app.services import auth_service, client_service, demande_service, email_service, limiteur, message_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/clients", tags=["Comptes clients"])

# Same answer whether or not the address is known: nothing is revealed.
REPONSE_NEUTRE = "Si cette adresse est valide, un e-mail vient de vous être envoyé."
LIEN_INVALIDE = "Ce lien est invalide ou a expiré"


def _envoyer(background_tasks: BackgroundTasks, fabriquer) -> None:
    try:
        background_tasks.add_task(email_service.envoyer, fabriquer())
    except KeyError:
        logger.exception("E-mail de compte non envoyé (variable EMAIL_* manquante)")


@router.post(
    "/inscription",
    response_model=MessageGenerique,
    summary="Créer un compte : un lien d'activation est envoyé par e-mail",
    dependencies=[limiteur.limite_ip("inscription", 5, 3600)],
)
def inscription(payload: InscriptionIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    brut = client_service.demander_activation(db, payload.email)
    if brut is None:
        _envoyer(background_tasks, lambda: email_service.messages_compte_existant(payload.email))
    else:
        _envoyer(background_tasks, lambda: email_service.messages_activation(payload.email, brut))
    return MessageGenerique(message=REPONSE_NEUTRE)


@router.post(
    "/activer",
    dependencies=[limiteur.limite_ip("activation", 10, 900)],
    response_model=TokenOut,
    summary="Choisir son mot de passe avec le lien reçu : active le compte et connecte",
    responses={400: {"description": LIEN_INVALIDE}},
)
def activer(payload: ActivationIn, db: Session = Depends(get_db)):
    try:
        client = client_service.activer(db, payload.token, payload.mot_de_passe)
    except client_service.LienInvalideError:
        raise HTTPException(status_code=400, detail=LIEN_INVALIDE)
    return TokenOut(token=auth_service.creer_jeton(client.id, client.email, "client", client_service.JETON_CLIENT_HEURES))


@router.post(
    "/connexion",
    dependencies=[limiteur.limite_ip("connexion-client", 10, 900)],
    response_model=TokenOut,
    summary="Se connecter (client)",
    responses={401: {"description": "E-mail ou mot de passe incorrect"}},
)
def connexion(payload: ConnexionIn, db: Session = Depends(get_db)):
    limiteur.verifier("connexion-client-compte", payload.email, 10, 900)
    try:
        return TokenOut(token=client_service.connexion(db, payload.email, payload.mot_de_passe))
    except auth_service.InvalidCredentialsError:
        raise HTTPException(status_code=401, detail="Identifiants invalides")


@router.post(
    "/mot-de-passe-oublie",
    response_model=MessageGenerique,
    summary="Recevoir un lien pour choisir un nouveau mot de passe",
    dependencies=[limiteur.limite_ip("mot-de-passe-oublie", 5, 3600)],
)
def mot_de_passe_oublie(payload: MotDePasseOublieIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Per mailbox too: nobody can flood one customer with mails from many addresses.
    limiteur.verifier("mot-de-passe-oublie-compte", payload.email, 3, 3600)
    brut = client_service.mot_de_passe_oublie(db, payload.email)
    if brut is not None:
        _envoyer(background_tasks, lambda: email_service.messages_reinitialisation(payload.email, brut))
    return MessageGenerique(message=REPONSE_NEUTRE)


@router.post(
    "/reinitialiser",
    dependencies=[limiteur.limite_ip("reinitialisation", 10, 900)],
    response_model=MessageGenerique,
    summary="Choisir un nouveau mot de passe avec le lien reçu",
    responses={400: {"description": LIEN_INVALIDE}},
)
def reinitialiser(payload: ReinitialisationIn, db: Session = Depends(get_db)):
    try:
        client_service.reinitialiser(db, payload.token, payload.mot_de_passe)
    except client_service.LienInvalideError:
        raise HTTPException(status_code=400, detail=LIEN_INVALIDE)
    return MessageGenerique(message="Mot de passe modifié")


@router.get(
    "/moi",
    response_model=MoiOut,
    summary="Mon compte : mes demandes et leurs messages non lus",
    responses={401: {"description": "Jeton client absent ou invalide"}},
)
def moi(db: Session = Depends(get_db), client: Client = Depends(require_client)):
    demandes = client_service.demandes_du_client(db, client)
    for demande in demandes:
        demande_service.appliquer_expiration(db, demande)
    non_lus = message_service.non_lus(db, [d.id for d in demandes], AuteurMessage.client)
    return MoiOut(
        email=client.email,
        demandes=[
            DemandeCompteOut(
                id=d.id,
                jeton=d.jeton,
                statut=d.statut,
                numero_affiche=d.numero_affiche,
                created_at=d.created_at,
                libelles=[l.libelle for l in d.lignes] or ["Projet libre"],
                total_indicatif=d.total_indicatif,
                total_final=d.total_final,
                messages_non_lus=non_lus.get(d.id, 0),
            )
            for d in demandes
        ],
    )


@router.post(
    "/moi/supprimer",
    status_code=204,
    summary="Supprimer mon compte (les demandes sont conservées par l'atelier)",
    responses={401: {"description": "Mot de passe incorrect"}},
)
def supprimer(payload: SupprimerCompteIn, db: Session = Depends(get_db), client: Client = Depends(require_client)):
    try:
        client_service.supprimer(db, client, payload.mot_de_passe)
    except auth_service.InvalidCredentialsError:
        raise HTTPException(status_code=401, detail="Mot de passe incorrect")
    return Response(status_code=204)
