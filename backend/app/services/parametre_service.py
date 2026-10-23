from sqlalchemy.orm import Session

from app.models.parametre import Parametre


def get(db: Session) -> Parametre:
    parametre = db.query(Parametre).first()
    if parametre is None:
        parametre = Parametre(email_commande_actif=False)
        db.add(parametre)
        db.commit()
        db.refresh(parametre)
    return parametre


def update(db: Session, data: dict) -> Parametre:
    parametre = get(db)
    parametre.email_commande_actif = data["email_commande_actif"]
    db.commit()
    db.refresh(parametre)
    return parametre
