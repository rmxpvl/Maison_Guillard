import { useState } from 'react'
import { Link } from 'react-router-dom'
import MentionDisponibilite from './MentionDisponibilite.jsx'
import { usePanier } from '../hooks/usePanier.js'
import { actionsFiche, prixAffiche } from '../utils/produit.js'

export default function InfosProduit({ produit }) {
  const { ajouter } = usePanier()
  const [ajoute, setAjoute] = useState(false)

  function ajouterAuPanier() {
    ajouter(produit)
    setAjoute(true)
  }

  return (
    <div className="infos">
      <h1>{produit.nom}</h1>
      <p className="infos__prix">{prixAffiche(produit)}</p>
      <MentionDisponibilite disponibilite={produit.disponibilite} />
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
        {actionsFiche(produit.disponibilite).map((action) =>
          action.code === 'panier' ? (
            <button
              key={action.libelle}
              type="button"
              className="bouton bouton--principal"
              onClick={ajouterAuPanier}
            >
              {action.libelle}
            </button>
          ) : (
            <button
              key={action.libelle}
              type="button"
              className={action.principale ? 'bouton bouton--principal' : 'bouton'}
              disabled
              title="Bientôt disponible"
            >
              {action.libelle}
            </button>
          ),
        )}
      </div>
      {ajoute && (
        <p className="infos__ajoute" role="status">
          Ajouté au panier. <Link to="/panier">Voir le panier</Link>
        </p>
      )}
    </div>
  )
}
