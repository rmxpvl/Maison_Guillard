import { Link } from 'react-router-dom'
import LigneArticlePanier from '../components/LigneArticlePanier.jsx'
import { usePanier } from '../hooks/usePanier.js'
import { formatPrix } from '../utils/produit.js'

export default function PagePanier() {
  const { lignes, changerQuantite, retirer, total } = usePanier()

  if (lignes.length === 0) {
    return (
      <section className="etat contenu">
        <h1>Votre panier est vide</h1>
        <Link to="/boutique">Découvrir la boutique</Link>
      </section>
    )
  }

  return (
    <section className="contenu section panier">
      <h1>Votre panier</h1>
      <ul className="panier__lignes">
        {lignes.map((ligne) => (
          <LigneArticlePanier
            key={ligne.produit_id}
            ligne={ligne}
            changerQuantite={changerQuantite}
            retirer={retirer}
          />
        ))}
      </ul>
      <p className="panier__total">Total : <strong>{formatPrix(total)}</strong></p>
      <p className="infos__note">Paiement et livraison convenus avec l'artisan après la commande.</p>
      <Link to="/commande" className="bouton bouton--principal">Passer commande</Link>
    </section>
  )
}
