from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.require_admin import require_admin
from app.routers.reponses import NON_AUTORISE
from app.schemas.parametre import ParametreIn, ParametreOut
from app.services import parametre_service

router = APIRouter(prefix="/api/parametres", tags=["Paramètres"])


@router.get(
    "",
    response_model=ParametreOut,
    summary="Lire les réglages du site",
    responses=NON_AUTORISE,
)
def get_parametres(db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    return parametre_service.get(db)


@router.put(
    "",
    response_model=ParametreOut,
    summary="Modifier les réglages du site",
    responses=NON_AUTORISE,
)
def update_parametres(
    payload: ParametreIn,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    return parametre_service.update(db, payload.model_dump())
