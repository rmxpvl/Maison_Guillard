import logging
import os
import smtplib
from email.message import EmailMessage

from app.models.commande import Commande
from app.models.devis import Devis

logger = logging.getLogger(__name__)


def _recapitulatif(commande: Commande) -> str:
    lignes = [
        f"- {ligne.produit.nom} x {ligne.quantite} : "
        f"{ligne.prix_unitaire_snapshot * ligne.quantite} €"
        for ligne in commande.lignes
    ]
    return "\n".join(lignes) + f"\n\nTotal : {commande.total} €"


def _message(destinataire: str, sujet: str, texte: str) -> EmailMessage:
    message = EmailMessage()
    message["From"] = os.environ["EMAIL_EXPEDITEUR"]
    message["To"] = destinataire
    message["Subject"] = sujet
    message.set_content(texte)
    return message


def messages_nouvelle_commande(commande: Commande) -> list[EmailMessage]:
    artisan = _message(
        os.environ["EMAIL_ARTISAN"],
        f"Nouvelle commande n°{commande.id}",
        f"Client : {commande.nom_client}\n"
        f"E-mail : {commande.email}\n"
        f"Téléphone : {commande.telephone or 'non renseigné'}\n"
        f"Adresse : {commande.adresse}\n\n"
        f"{_recapitulatif(commande)}\n",
    )
    client = _message(
        commande.email,
        f"Maison Guillard : commande n°{commande.id} reçue",
        f"Bonjour {commande.nom_client},\n\n"
        f"Nous avons bien reçu votre commande n°{commande.id} :\n\n"
        f"{_recapitulatif(commande)}\n\n"
        "Maison Guillard vous contacte sous 48 h pour le paiement et la livraison.\n",
    )
    return [artisan, client]


def envoyer(messages: list[EmailMessage]) -> None:
    # Runs after the response: an email problem must never cancel an order.
    try:
        with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ["SMTP_PORT"]), timeout=10) as serveur:
            serveur.starttls()
            serveur.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
            for message in messages:
                serveur.send_message(message)
    except Exception:
        logger.exception("Envoi des e-mails de commande impossible")


def messages_nouveau_devis(devis: Devis) -> list[EmailMessage]:
    sujet = devis.produit.nom if devis.produit else "Projet sur mesure"
    artisan = _message(
        os.environ["EMAIL_ARTISAN"],
        f"Nouvelle demande de devis n°{devis.id}",
        f"Client : {devis.nom_client}\n"
        f"E-mail : {devis.email}\n"
        f"Téléphone : {devis.telephone or 'non renseigné'}\n"
        f"À propos de : {sujet}\n\n"
        f"{devis.description_projet}\n",
    )
    client = _message(
        devis.email,
        f"Maison Guillard : demande de devis n°{devis.id} reçue",
        f"Bonjour {devis.nom_client},\n\n"
        f"Nous avons bien reçu votre demande de devis n°{devis.id} ({sujet}).\n\n"
        "Maison Guillard vous répond sous 48 h.\n",
    )
    return [artisan, client]
