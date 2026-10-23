from sqlalchemy.orm import Session

from app.models.commande import Commande, LigneCommande
from app.models.produit import Disponibilite, Produit


class ProduitIntrouvableError(Exception):
    """Raised when an order line references a produit that does not exist."""

    def __init__(self, produit_id: int):
        super().__init__(produit_id)
        self.produit_id = produit_id


class ProduitIndisponibleError(Exception):
    """Raised when an order line references a produit that is not 'disponible'."""

    def __init__(self, produit: Produit):
        super().__init__(produit.id)
        self.produit_id = produit.id
        self.nom = produit.nom


def create(db: Session, data: dict) -> Commande:
    lignes = []
    for ligne in data["lignes"]:
        produit = db.query(Produit).filter(Produit.id == ligne["produit_id"]).first()
        if produit is None:
            raise ProduitIntrouvableError(ligne["produit_id"])
        if produit.disponibilite != Disponibilite.disponible:
            raise ProduitIndisponibleError(produit)
        # The price comes from the database, never from the request.
        lignes.append(
            LigneCommande(
                produit_id=produit.id,
                quantite=ligne["quantite"],
                prix_unitaire_snapshot=produit.prix,
            )
        )

    commande = Commande(
        nom_client=data["nom_client"],
        email=data["email"],
        telephone=data.get("telephone"),
        adresse=data["adresse"],
        lignes=lignes,
    )
    db.add(commande)
    db.commit()
    db.refresh(commande)
    return commande
