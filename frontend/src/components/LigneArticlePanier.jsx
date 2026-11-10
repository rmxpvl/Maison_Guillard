import { Link } from 'react-router-dom'
import { QUANTITE_MAX, SOUHAIT_MAX } from '../utils/panier.js'
import { formatPrix } from '../utils/produit.js'

const QUANTITES = Array.from({ length: QUANTITE_MAX }, (_, i) => i + 1)

// One line of « Ma demande »: quantity, finish and wish are editable.
export default function LigneArticlePanier({ ligne, changerQuantite, changerTeinte, changerSouhait, retirer }) {
  const teinte = ligne.teintes.find((t) => t.id === ligne.teinte_id)
  return (
    <li className="ligne-panier">
      {ligne.photo ? (
        <img src={ligne.photo} alt="" className="ligne-panier__photo" />
      ) : (
        <div className="ligne-panier__photo photo-vide" aria-hidden="true" />
      )}
      <div className="ligne-panier__infos">
        <Link to={`/produits/${ligne.produit_id}`}>{ligne.nom}</Link>
        <span>À partir de {formatPrix(ligne.prix)}</span>
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
      <span className="ligne-panier__sous-total">À partir de {formatPrix(Number(ligne.prix) * ligne.quantite)}</span>
      <button type="button" className="bouton bouton--discret" onClick={() => retirer(ligne.produit_id)}>
        Retirer
      </button>
      <div className="ligne-panier__perso">
        {ligne.teintes.length > 0 && (
          <label className="ligne-panier__teinte">
            Finition
            {teinte && <img src={teinte.image_url} alt="" className="teinte__image" />}
            <select
              value={ligne.teinte_id ?? ''}
              onChange={(e) => changerTeinte(ligne.produit_id, e.target.value)}
            >
              <option value="">Pas de préférence</option>
              {ligne.teintes.map((t) => <option key={t.id} value={t.id}>{t.nom}</option>)}
            </select>
          </label>
        )}
        <label className="ligne-panier__souhait">
          Votre souhait pour cette pièce
          <textarea
            rows={2}
            maxLength={SOUHAIT_MAX}
            value={ligne.souhait}
            onChange={(e) => changerSouhait(ligne.produit_id, e.target.value)}
            placeholder="Dimensions, détail, usage…"
          />
        </label>
      </div>
    </li>
  )
}
