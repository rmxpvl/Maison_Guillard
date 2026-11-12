from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.demande import Demande, LigneDemande, StatutDemande
from app.models.devis_numero import CompteurDevis
from app.services import demande_service, reglages_service

S = StatutDemande
STATUTS_ENVOI = {S.nouvelle, S.devis_envoye, S.expiree}  # a quote can be (re)sent until paid


class ReglagesIncompletsError(Exception):
    def __init__(self, manquants: list[str]):
        super().__init__(", ".join(manquants))
        self.manquants = manquants


class StatutDevisInterditError(Exception):
    pass


class LigneDevisInvalideError(Exception):
    pass


@dataclass
class LigneVue:
    libelle: str
    quantite: int
    teinte_nom: str | None
    souhait: str | None
    prix_unitaire: Decimal
    dimensions: str | None = None
    teinte_couleur: str | None = None  # #rrggbb, for the swatch


@dataclass
class VueDevis:
    """Everything a quote shows. The PDF, the e-mail and the preview all come from this."""

    numero: str | None  # None for a preview: the number is given when the quote is sent
    version: int
    client_nom: str
    client_adresse: str | None
    emis_le: datetime
    expire_le: datetime
    lignes: list[LigneVue]
    frais_livraison: Decimal
    message: str | None
    entreprise: dict
    conditions: dict
    client_email: str | None = None
    client_telephone: str | None = None
    demande_id: int | None = None
    demande_date: datetime | None = None
    accepte_le: datetime | None = None  # set once the customer has accepted online (payment lot)
    cgv_version: str | None = None

    @property
    def numero_affiche(self) -> str | None:
        if self.numero is None:
            return None
        return self.numero if self.version <= 1 else f"{self.numero}-v{self.version}"

    @property
    def sous_total(self) -> Decimal:
        return sum((l.prix_unitaire * l.quantite for l in self.lignes), Decimal("0"))

    @property
    def total(self) -> Decimal:
        return self.sous_total + self.frais_livraison


def prochain_numero(db: Session, annee: int) -> str:
    """Atomic upsert: two simultaneous sends can never get the same number."""
    table = CompteurDevis.__table__
    requete = (
        pg_insert(table)
        .values(annee=annee, dernier=1)
        .on_conflict_do_update(index_elements=[table.c.annee], set_={"dernier": table.c.dernier + 1})
        .returning(table.c.dernier)
    )
    return f"D-{annee}-{db.execute(requete).scalar_one():04d}"


def _valider(demande: Demande, data: dict) -> dict[int, Decimal]:
    """Every catalogue line needs exactly one final price; the quote needs at least one line."""
    attendues = {l.id for l in demande.lignes if l.produit_id is not None}
    prix = {l["id"]: l["prix_final"] for l in data["lignes"]}
    if set(prix) != attendues or len(prix) != len(data["lignes"]):
        raise LigneDevisInvalideError("Chaque pièce de la demande doit avoir un prix final")
    if not attendues and not data["lignes_libres"]:
        raise LigneDevisInvalideError("Le devis doit contenir au moins une ligne")
    return prix


def _lignes_vue(demande: Demande, prix: dict[int, Decimal], libres: list[dict]) -> list[LigneVue]:
    vues = [
        LigneVue(l.libelle, l.quantite, l.teinte_nom, l.souhait, prix[l.id], l.dimensions, l.teinte_couleur)
        for l in demande.lignes
        if l.produit_id is not None
    ]
    vues += [LigneVue(l["libelle"], l["quantite"], None, None, l["prix"]) for l in libres]
    return vues


def vue_depuis_demande(demande: Demande) -> VueDevis | None:
    """The quote as it was sent (frozen prices, frozen company identity)."""
    if demande.numero_devis is None or demande.devis_snapshot is None:
        return None
    return VueDevis(
        numero=demande.numero_devis,
        version=demande.version_devis,
        client_nom=demande.nom_client,
        client_adresse=demande.adresse,
        emis_le=demande.devis_envoye_at,
        expire_le=demande.expire_at,
        lignes=[
            LigneVue(l.libelle, l.quantite, l.teinte_nom, l.souhait, l.prix_final or Decimal("0"), l.dimensions, l.teinte_couleur)
            for l in demande.lignes
        ],
        frais_livraison=demande.frais_livraison or Decimal("0"),
        message=demande.message_artisane,
        entreprise=demande.devis_snapshot["entreprise"],
        conditions=demande.devis_snapshot["conditions"],
        client_email=demande.email,
        client_telephone=demande.telephone,
        demande_id=demande.id,
        demande_date=demande.created_at,
        accepte_le=demande.cgv_acceptees_at,
        cgv_version=demande.cgv_version,
    )


def apercu(db: Session, demande_id: int, data: dict) -> VueDevis | None:
    """The quote the artisane is editing, without saving anything."""
    demande = demande_service.get_by_id(db, demande_id)
    if demande is None:
        return None
    prix = _valider(demande, data)
    reglages = reglages_service.get(db)
    maintenant = datetime.now(timezone.utc)
    cadre = reglages_service.snapshot(reglages)
    return VueDevis(
        numero=demande.numero_devis,
        version=demande.version_devis + 1 if demande.numero_devis else 1,
        client_nom=demande.nom_client,
        client_adresse=demande.adresse,
        emis_le=maintenant,
        expire_le=maintenant + timedelta(days=reglages.validite_jours),
        lignes=_lignes_vue(demande, prix, data["lignes_libres"]),
        frais_livraison=data["frais_livraison"],
        message=data.get("message_artisane"),
        entreprise=cadre["entreprise"],
        conditions=cadre["conditions"],
        client_email=demande.email,
        client_telephone=demande.telephone,
        demande_id=demande.id,
        demande_date=demande.created_at,
    )


def envoyer(db: Session, demande_id: int, data: dict) -> Demande | None:
    demande = demande_service.get_by_id(db, demande_id)
    if demande is None:
        return None
    if demande.statut not in STATUTS_ENVOI:
        raise StatutDevisInterditError()

    reglages = reglages_service.get(db)
    manquants = reglages_service.champs_manquants(reglages)
    if manquants:
        raise ReglagesIncompletsError(manquants)
    prix = _valider(demande, data)

    maintenant = datetime.now(timezone.utc)
    if demande.numero_devis is None:
        demande.numero_devis = prochain_numero(db, maintenant.year)
        demande.version_devis = 1
    else:
        demande.version_devis += 1

    for ligne in list(demande.lignes):
        if ligne.produit_id is None:
            demande.lignes.remove(ligne)  # free lines are replaced by the ones being sent
        else:
            ligne.prix_final = prix[ligne.id]
    for libre in data["lignes_libres"]:
        demande.lignes.append(
            LigneDemande(libelle=libre["libelle"], quantite=libre["quantite"], prix_final=libre["prix"])
        )

    demande.frais_livraison = data["frais_livraison"]
    demande.message_artisane = data.get("message_artisane")
    demande.devis_envoye_at = maintenant
    demande.expire_at = maintenant + timedelta(days=reglages.validite_jours)
    demande.devis_snapshot = reglages_service.snapshot(reglages)
    demande.statut = StatutDemande.devis_envoye
    db.commit()
    db.refresh(demande)
    return demande


def refuser(db: Session, jeton: str) -> Demande | None:
    demande = demande_service.get_by_jeton(db, jeton)  # applies the lazy expiry first
    if demande is None:
        return None
    if demande.statut != StatutDemande.devis_envoye:
        raise StatutDevisInterditError()
    demande.statut = StatutDemande.refusee
    db.commit()
    db.refresh(demande)
    return demande
