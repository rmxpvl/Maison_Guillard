import { useState } from 'react'
import { Link } from 'react-router-dom'
import ChoixTeinte from './ChoixTeinte.jsx'
import { usePanier } from '../hooks/usePanier.js'
import { prixAffiche, teintesVisibles } from '../utils/produit.js'

export default function InfosProduit({ produit }) {
  const { ajouter } = usePanier()
  const [ajoute, setAjoute] = useState(false)
  const teintes = teintesVisibles(produit)
  const [teinteId, setTeinteId] = useState(() => teintes.find((t) => t.nom === 'Naturel')?.id ?? null)

  function ajouterAuPanier() {
    ajouter(produit)
    setAjoute(true)
  }

  return (
    <div className="infos">
      <h1>{produit.nom}</h1>
      <p className="infos__prix">{prixAffiche(produit)}</p>
      <dl className="infos__details">
        <dt>Dimensions</dt>
        <dd>{produit.dimensions}</dd>
      </dl>
      <p>{produit.description}</p>
      <ChoixTeinte teintes={teintes} valeur={teinteId} onChange={setTeinteId} />
      {teintes.length > 0 && (
        <p className="infos__note">
          Le prix final peut varier selon la finition et vos souhaits ; il est confirmé dans votre devis.
        </p>
      )}
      <div className="infos__actions">
        <button type="button" className="bouton bouton--principal" onClick={ajouterAuPanier}>
          Ajouter au panier
        </button>
        <Link to={`/contact?produit=${produit.id}`} className="bouton">
          Une question ? Contactez l'atelier
        </Link>
      </div>
      {ajoute && (
        <p className="infos__ajoute" role="status">
          Ajouté au panier. <Link to="/panier">Voir le panier</Link>
        </p>
      )}
      <p className="infos__note">
        Fabriqué à la commande · Fabrication et livraison garanties sous 15 jours après paiement
      </p>
    </div>
  )
}
