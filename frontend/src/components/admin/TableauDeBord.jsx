import { useState } from 'react'
import { Link } from 'react-router-dom'
import EtatChargement from '../EtatChargement.jsx'
import { useResumeAdmin } from '../../hooks/useResumeAdmin.js'
import { nombreEtMot, resumeTaches } from '../../utils/admin.js'

const GUIDE = [
  'Un client envoie une demande depuis le site.',
  'Vous lui envoyez un devis avec vos prix.',
  'Il l’accepte et le paie en ligne : vous êtes prévenue par e-mail.',
  'Vous fabriquez, puis vous marquez la commande comme expédiée.',
  'Elle arrive chez le client : la commande est terminée.',
]

// « Aujourd'hui »: what waits for the artisane, most urgent first. Each line says what to do
// and takes her to the right place.
function listeTaches(r) {
  const taches = []
  if (r.livraisonsEnRetard > 0) {
    taches.push({
      cle: 'retard', ton: 'alerte', nombre: r.livraisonsEnRetard, filtre: 'cours',
      titre: r.livraisonsEnRetard > 1 ? 'livraisons en retard' : 'livraison en retard',
      aide: 'La date promise au client est dépassée. Regardez où en est la commande.',
    })
  }
  if (r.livraisonsProches > 0) {
    taches.push({
      cle: 'proche', ton: 'attention', nombre: r.livraisonsProches, filtre: 'afaire',
      titre: r.livraisonsProches > 1 ? 'livraisons à tenir sous 3 jours' : 'livraison à tenir sous 3 jours',
      aide: 'Ces commandes doivent partir très bientôt.',
    })
  }
  if (r.messages > 0) {
    taches.push({
      cle: 'messages', ton: 'attention', nombre: r.messages, filtre: 'messages',
      titre: r.messages > 1 ? 'messages de clients à lire' : 'message de client à lire',
      aide: 'Un client attend votre réponse.',
    })
  }
  if (r.aChiffrer > 0) {
    taches.push({
      cle: 'chiffrer', ton: 'attention', nombre: r.aChiffrer, filtre: 'nouvelle',
      titre: r.aChiffrer > 1 ? 'demandes à chiffrer' : 'demande à chiffrer',
      aide: 'Des clients attendent votre devis : indiquez vos prix et envoyez-le.',
    })
  }
  if (r.aLancer > 0) {
    taches.push({
      cle: 'lancer', ton: 'attention', nombre: r.aLancer, filtre: 'payee',
      titre: r.aLancer > 1 ? 'commandes payées à lancer' : 'commande payée à lancer',
      aide: 'Le paiement est reçu : vous pouvez commencer la fabrication.',
    })
  }
  if (r.aExpedier > 0) {
    taches.push({
      cle: 'expedier', ton: 'cours', nombre: r.aExpedier, filtre: 'en_fabrication',
      titre: r.aExpedier > 1 ? 'commandes en fabrication' : 'commande en fabrication',
      aide: 'Marquez-les comme expédiées quand elles partent : le client en est informé.',
    })
  }
  return taches
}

export default function TableauDeBord() {
  const { statut, demandes, reessayer } = useResumeAdmin()
  const resume = resumeTaches(demandes)
  const taches = listeTaches(resume)
  const [date] = useState(() => new Intl.DateTimeFormat('fr-FR', { dateStyle: 'full' }).format(new Date()))

  return (
    <div className="page-admin">
      <header className="page-admin__entete">
        <div>
          <h1>Bonjour !</h1>
          <p className="page-admin__intro">Voici ce qui vous attend. Nous sommes le {date}.</p>
        </div>
        <Link to="/admin/produits/nouveau" className="bouton bouton--principal">Ajouter un produit</Link>
      </header>

      <EtatChargement statut={statut} reessayer={reessayer}>
        <section aria-labelledby="titre-afaire">
          <h2 id="titre-afaire">À faire</h2>
          {taches.length === 0 ? (
            <p className="tout-va-bien">
              Tout est à jour : rien n’attend votre action pour le moment.
              {resume.attente > 0 && ` ${nombreEtMot(resume.attente, 'devis est', 'devis sont')} en attente de la réponse d’un client.`}
            </p>
          ) : (
            <ul className="taches">
              {taches.map((t) => (
                <li key={t.cle} className={`tache tache--${t.ton}`}>
                  <span className="tache__nombre">{t.nombre}</span>
                  <span className="tache__texte">
                    <strong>{t.titre}</strong>
                    <span>{t.aide}</span>
                  </span>
                  <Link to={`/admin?onglet=demandes&filtre=${t.filtre}`} className="bouton">Voir</Link>
                </li>
              ))}
            </ul>
          )}
          {taches.length > 0 && resume.attente > 0 && (
            <p className="page-admin__intro">
              {nombreEtMot(resume.attente, 'devis envoyé attend', 'devis envoyés attendent')} la réponse du client : rien à faire de votre côté.
            </p>
          )}
        </section>
      </EtatChargement>

      <section aria-labelledby="titre-guide" className="guide">
        <h2 id="titre-guide">Comment se passe une commande</h2>
        <ol className="guide__etapes">
          {GUIDE.map((texte) => <li key={texte}>{texte}</li>)}
        </ol>
        <p className="page-admin__intro">
          Besoin de modifier un prix, une photo ou une finition ? Ouvrez <Link to="/admin?onglet=produits">Produits</Link>.
        </p>
      </section>
    </div>
  )
}
