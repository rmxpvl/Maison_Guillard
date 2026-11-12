from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.require_admin import require_admin
from app.routers.reponses import NON_AUTORISE
from app.schemas.reglages import MessageTypeIn, MessageTypeOut, ReglagesDevis
from app.services import reglages_service

router = APIRouter(prefix="/api", tags=["Réglages du devis"])

MESSAGE_INTROUVABLE = {404: {"description": "Message type introuvable"}}


@router.get("/reglages-devis", response_model=ReglagesDevis, summary="Voir les réglages du devis", responses=NON_AUTORISE)
def get_reglages(db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    return reglages_service.get(db)


@router.put("/reglages-devis", response_model=ReglagesDevis, summary="Modifier les réglages du devis", responses=NON_AUTORISE)
def put_reglages(payload: ReglagesDevis, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    return reglages_service.update(db, payload.model_dump())


@router.get("/messages-types", response_model=list[MessageTypeOut], summary="Lister les messages types", responses=NON_AUTORISE)
def list_messages_types(db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    return reglages_service.messages_types(db)


@router.post("/messages-types", response_model=MessageTypeOut, status_code=201, summary="Créer un message type", responses=NON_AUTORISE)
def create_message_type(payload: MessageTypeIn, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    return reglages_service.creer_message_type(db, payload.model_dump())


@router.put(
    "/messages-types/{message_id}",
    response_model=MessageTypeOut,
    summary="Modifier un message type",
    responses={**NON_AUTORISE, **MESSAGE_INTROUVABLE},
)
def update_message_type(
    message_id: int, payload: MessageTypeIn, db: Session = Depends(get_db), admin: dict = Depends(require_admin)
):
    message = reglages_service.modifier_message_type(db, message_id, payload.model_dump())
    if message is None:
        raise HTTPException(status_code=404, detail="Message type introuvable")
    return message


@router.delete(
    "/messages-types/{message_id}",
    status_code=204,
    summary="Supprimer un message type",
    responses={**NON_AUTORISE, **MESSAGE_INTROUVABLE},
)
def delete_message_type(message_id: int, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    if not reglages_service.supprimer_message_type(db, message_id):
        raise HTTPException(status_code=404, detail="Message type introuvable")
    return Response(status_code=204)
