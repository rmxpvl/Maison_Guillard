import logging
import os
import smtplib
from email.message import EmailMessage

from app.models.demande import Demande

logger = logging.getLogger(__name__)


def _recapitulatif(demande: Demande) -> str:
    if not demande.lignes:
        return f"Projet : {demande.description_projet}"
    blocs = []
    for ligne in demande.lignes:
        texte = f"- {ligne.libelle} x {ligne.quantite} : à partir de {ligne.prix_indicatif * ligne.quantite} €"
        if ligne.teinte_nom:
            texte += f"\n  Finition : {ligne.teinte_nom}"
        if ligne.souhait:
            texte += f"\n  Souhait : {ligne.souhait}"
        blocs.append(texte)
    return "\n".join(blocs) + f"\n\nTotal indicatif : à partir de {demande.total_indicatif} €, hors livraison"


def _message(destinataire: str, sujet: str, texte: str) -> EmailMessage:
    message = EmailMessage()
    message["From"] = os.environ["EMAIL_EXPEDITEUR"]
    message["To"] = destinataire
    message["Subject"] = sujet
    message.set_content(texte)
    return message


def lien_demande(demande: Demande) -> str:
    site = os.environ.get("SITE_URL", "http://localhost:5173").rstrip("/")
    return f"{site}/devis/{demande.jeton}"


def messages_nouvelle_demande(demande: Demande) -> list[EmailMessage]:
    artisan = _message(
        os.environ["EMAIL_ARTISAN"],
        f"Nouvelle demande n°{demande.id}",
        f"Client : {demande.nom_client}\n"
        f"E-mail : {demande.email}\n"
        f"Téléphone : {demande.telephone or 'non renseigné'}\n"
        f"Adresse : {demande.adresse or 'non renseignée'}\n"
        f"Message : {demande.message_client or '-'}\n\n"
        f"{_recapitulatif(demande)}\n",
    )
    client = _message(
        demande.email,
        f"Maison Guillard : demande n°{demande.id} reçue",
        f"Bonjour {demande.nom_client},\n\n"
        f"Nous avons bien reçu votre demande n°{demande.id} :\n\n"
        f"{_recapitulatif(demande)}\n\n"
        "Rien n'est payé maintenant : Maison Guillard vous envoie votre devis sous 48 h.\n"
        f"Suivez votre demande ici : {lien_demande(demande)}\n",
    )
    return [artisan, client]


def messages_devis(demande: Demande, pdf: bytes) -> list[EmailMessage]:
    """The quote for the customer: link to the secret page, expiry date and the PDF attached."""
    message = _message(
        demande.email,
        f"Maison Guillard : votre devis {demande.numero_devis}",
        f"Bonjour {demande.nom_client},\n\n"
        f"Votre devis {demande.numero_devis} est prêt (en pièce jointe, et en ligne).\n"
        f"Il est valable jusqu'au {demande.expire_at.strftime('%d/%m/%Y')}.\n\n"
        "Fabrication et livraison garanties sous 15 jours après le paiement.\n"
        f"Consulter, accepter ou refuser le devis : {lien_demande(demande)}\n",
    )
    message.add_attachment(
        pdf, maintype="application", subtype="pdf", filename=f"devis-{demande.numero_devis}.pdf"
    )
    return [message]


def messages_devis_refuse(demande: Demande) -> list[EmailMessage]:
    return [
        _message(
            os.environ["EMAIL_ARTISAN"],
            f"Devis {demande.numero_devis} refusé par le client",
            f"{demande.nom_client} ({demande.email}) a refusé le devis {demande.numero_devis} "
            f"de la demande n°{demande.id}.\n",
        )
    ]


def envoyer(messages: list[EmailMessage]) -> None:
    # Runs after the response: an email problem must never cancel a request.
    try:
        with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ["SMTP_PORT"]), timeout=10) as serveur:
            serveur.starttls()
            serveur.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
            for message in messages:
                serveur.send_message(message)
    except Exception:
        logger.exception("Envoi des e-mails impossible")
