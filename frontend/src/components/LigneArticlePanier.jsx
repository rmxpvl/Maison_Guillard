import { Link } from 'react-router-dom'
import { QUANTITE_MAX } from '../utils/panier.js'
import { formatPrix } from '../utils/produit.js'

const QUANTITES = Array.from({ length: QUANTITE_MAX }, (_, i) => i + 1)

export default function LigneArticlePanier({ ligne, changerQuantite, retirer }) {
  return (
    <li className="ligne-panier">
      {ligne.photo ? (
        <img src={ligne.photo} alt="" className="ligne-panier__photo" />
      ) : (
        <div className="ligne-panier__photo photo-vide" aria-hidden="true" />
      )}
      <div className="ligne-panier__infos">
        <Link to={`/produits/${ligne.produit_id}`}>{ligne.nom}</Link>
        <span>{formatPrix(ligne.prix)}</span>
      </div>
      <label className="ligne-panier__quantite">
        Quantité
        <select
          value={ligne.quantite}
          onChange={(e) => changerQuantite(ligne.produit_id, e.target.value)}
        >
          {QUANTITES.map((q) => <option key={q} value={q}>{q}</option>)}
        </select>
      </label>
      <span className="ligne-panier__sous-total">{formatPrix(Number(ligne.prix) * ligne.quantite)}</span>
      <button type="button" className="bouton bouton--discret" onClick={() => retirer(ligne.produit_id)}>
        Retirer
      </button>
    </li>
  )
}
