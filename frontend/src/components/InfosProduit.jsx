import BadgeDisponibilite from './BadgeDisponibilite.jsx'
import { actionsFiche, prixAffiche } from '../utils/produit.js'

export default function InfosProduit({ produit }) {
  return (
    <div className="infos">
      <h1>{produit.nom}</h1>
      <p className="infos__prix">{prixAffiche(produit)}</p>
      <BadgeDisponibilite disponibilite={produit.disponibilite} />
      {produit.disponibilite === 'sur_commande' && (
        <p className="infos__note">
          Fabriqué à la demande : prix et délai confirmés par l'artisan sur devis.
        </p>
      )}
      <dl className="infos__details">
        <dt>Dimensions</dt>
        <dd>{produit.dimensions}</dd>
      </dl>
      <p>{produit.description}</p>
      <div className="infos__actions">
        {actionsFiche(produit.disponibilite).map((action) => (
          <button
            key={action.libelle}
            type="button"
            className={action.principale ? 'bouton bouton--principal' : 'bouton'}
            disabled
            title="Bientôt disponible"
          >
            {action.libelle}
          </button>
        ))}
      </div>
    </div>
  )
}
