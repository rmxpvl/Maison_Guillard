from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.require_admin import require_admin
from app.routers.reponses import NON_AUTORISE, STOCKAGE_INDISPONIBLE
from app.schemas.contenu import ContenuOut, ContenuPublicOut, TexteIn
from app.services import contenu_service, photo_service

router = APIRouter(prefix="/api/contenus", tags=["Contenus du site"])

CLE_INCONNUE = {404: {"description": "Ce contenu n'existe pas"}}
MAUVAIS_TYPE = {422: {"description": "Ce contenu n'est pas du bon type (texte ou photo)"}}


def _sortie(ligne) -> ContenuOut:
    return ContenuOut(cle=ligne.cle, texte=ligne.texte, image_url=ligne.image_url)


@router.get(
    "",
    response_model=dict[str, ContenuPublicOut],
    summary="Les textes et photos modifiés des pages publiques (les autres gardent leur valeur d'origine)",
)
def lire(db: Session = Depends(get_db)):
    return {cle: ContenuPublicOut(texte=c.texte, image_url=c.image_url) for cle, c in contenu_service.tous(db).items()}


@router.put(
    "/{cle}",
    response_model=ContenuOut,
    summary="Modifier un texte (vide : retour au texte d'origine)",
    responses={**NON_AUTORISE, **CLE_INCONNUE, **MAUVAIS_TYPE},
)
def modifier_texte(cle: str, payload: TexteIn, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    try:
        return _sortie(contenu_service.definir_texte(db, cle, payload.texte))
    except contenu_service.CleInconnueError:
        raise HTTPException(status_code=404, detail="Ce contenu n'existe pas")
    except contenu_service.MauvaisTypeError:
        raise HTTPException(status_code=422, detail="Ce contenu est une photo, pas un texte")


@router.post(
    "/{cle}/image",
    response_model=ContenuOut,
    summary="Changer une photo",
    responses={**NON_AUTORISE, **CLE_INCONNUE, **MAUVAIS_TYPE},
)
def changer_image(cle: str, fichier: UploadFile = File(...), db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    try:
        contenu_service._verifier(cle, contenu_service.IMAGE)  # refuse a wrong key before storing the file
    except contenu_service.CleInconnueError:
        raise HTTPException(status_code=404, detail="Ce contenu n'existe pas")
    except contenu_service.MauvaisTypeError:
        raise HTTPException(status_code=422, detail="Ce contenu est un texte, pas une photo")
    try:
        url = photo_service.upload_to_cloudinary(fichier)
    except photo_service.ImageInvalideError as erreur:
        raise HTTPException(status_code=422, detail=str(erreur))
    except photo_service.StockageIndisponibleError:
        raise HTTPException(status_code=502, detail=STOCKAGE_INDISPONIBLE)
    return _sortie(contenu_service.definir_image(db, cle, url))


@router.delete(
    "/{cle}",
    status_code=204,
    summary="Revenir au texte ou à la photo d'origine",
    responses={**NON_AUTORISE, **CLE_INCONNUE},
)
def retablir(cle: str, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    try:
        contenu_service.retablir(db, cle)
    except contenu_service.CleInconnueError:
        raise HTTPException(status_code=404, detail="Ce contenu n'existe pas")
    return Response(status_code=204)
