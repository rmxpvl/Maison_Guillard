import secrets
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.categorie import Categorie
from app.models.demande import Demande, LigneDemande, StatutDemande
from app.models.produit import Produit

S = StatutDemande

# Moves the artisane may make by hand. Payment, refusal and expiry have their own flows.
TRANSITIONS_ADMIN = {
    S.nouvelle: {S.annulee},
    S.devis_envoye: {S.annulee},
    S.payee: {S.en_fabrication},
    S.en_fabrication: {S.expediee},
    S.expediee: {S.livree},
}


class ProduitIntrouvableError(Exception):
    def __init__(self, produit_id: int):
        super().__init__(produit_id)
        self.produit_id = produit_id


class ProduitMasqueError(Exception):
    """Raised when a requested produit is hidden: it cannot be requested any more."""

    def __init__(self, produit: Produit):
        super().__init__(produit.id)
        self.nom = produit.nom


class TeinteNonProposeeError(Exception):
    def __init__(self, produit: Produit):
        super().__init__(produit.id)
        self.nom = produit.nom


class TransitionInterditeError(Exception):
    pass


def transition_autorisee(depart: StatutDemande, arrivee: StatutDemande) -> bool:
    return arrivee in TRANSITIONS_ADMIN.get(depart, set())


def _nouveau_jeton() -> str:
    return secrets.token_urlsafe(32)


def _ligne(db: Session, entree: dict) -> LigneDemande:
    produit = db.query(Produit).filter(Produit.id == entree["produit_id"]).first()
    if produit is None:
        raise ProduitIntrouvableError(entree["produit_id"])
    if not produit.visible:
        raise ProduitMasqueError(produit)

    teinte = None
    if entree.get("teinte_id") is not None:
        teinte = next((t for t in produit.teintes if t.id == entree["teinte_id"] and t.active), None)
        if teinte is None:
            raise TeinteNonProposeeError(produit)

    # Name and price are copied: the request must not change when the catalogue does.
    return LigneDemande(
        produit_id=produit.id,
        libelle=produit.nom,
        quantite=entree["quantite"],
        teinte_id=teinte.id if teinte else None,
        teinte_nom=teinte.nom if teinte else None,
        souhait=entree.get("souhait") or None,
        prix_indicatif=produit.prix,
    )


def create(db: Session, data: dict) -> Demande:
    lignes = [_ligne(db, entree) for entree in data["lignes"]]
    demande = Demande(
        jeton=_nouveau_jeton(),
        nom_client=data["nom_client"],
        email=data["email"],
        telephone=data.get("telephone"),
        adresse=data["adresse"],
        message_client=data.get("message_client"),
        lignes=lignes,
    )
    db.add(demande)
    db.commit()
    db.refresh(demande)
    return demande


def create_projet_libre(db: Session, data: dict) -> Demande:
    produit_id = data.get("produit_id")
    if produit_id is not None and db.query(Produit).filter(Produit.id == produit_id).first() is None:
        raise ProduitIntrouvableError(produit_id)

    demande = Demande(
        jeton=_nouveau_jeton(),
        nom_client=data["nom_client"],
        email=data["email"],
        telephone=data.get("telephone"),
        adresse=data.get("adresse"),
        description_projet=data["description_projet"],
        produit_reference_id=produit_id,
    )
    db.add(demande)
    db.commit()
    db.refresh(demande)
    return demande


def appliquer_expiration(db: Session, demande: Demande) -> None:
    """Lazy expiry: no scheduled job, an overdue quote becomes « expirée » when it is read."""
    if (
        demande.statut == StatutDemande.devis_envoye
        and demande.expire_at is not None
        and demande.expire_at <= datetime.now(timezone.utc)
    ):
        demande.statut = StatutDemande.expiree
        db.commit()


def get_all(db: Session, statut: StatutDemande | None = None) -> list[Demande]:
    query = db.query(Demande)
    if statut is not None:
        query = query.filter(Demande.statut == statut)
    demandes = query.order_by(Demande.id.desc()).all()
    for demande in demandes:
        appliquer_expiration(db, demande)
    if statut is not None:
        demandes = [d for d in demandes if d.statut == statut]
    return demandes


def get_by_id(db: Session, demande_id: int) -> Demande | None:
    demande = db.query(Demande).filter(Demande.id == demande_id).first()
    if demande is not None:
        appliquer_expiration(db, demande)
    return demande


def get_by_jeton(db: Session, jeton: str) -> Demande | None:
    demande = db.query(Demande).filter(Demande.jeton == jeton).first()
    if demande is not None:
        appliquer_expiration(db, demande)
    return demande


def univers_de(db: Session, demande: Demande) -> list[str]:
    """Univers (codes) of the catalogue pieces of a request."""
    ids = [l.produit_id for l in demande.lignes if l.produit_id is not None]
    if not ids:
        return []
    lignes = (
        db.query(Categorie.univers)
        .join(Produit, Produit.categorie_id == Categorie.id)
        .filter(Produit.id.in_(ids))
        .distinct()
        .all()
    )
    return [univers.value for (univers,) in lignes]


def changer_statut(db: Session, demande_id: int, statut: StatutDemande) -> Demande | None:
    demande = get_by_id(db, demande_id)
    if demande is None:
        return None
    if not transition_autorisee(demande.statut, statut):
        raise TransitionInterditeError()
    demande.statut = statut
    db.commit()
    db.refresh(demande)
    return demande
