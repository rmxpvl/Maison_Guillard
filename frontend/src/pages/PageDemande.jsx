import { Link } from 'react-router-dom'
import LigneArticlePanier from '../components/LigneArticlePanier.jsx'
import { usePanier } from '../hooks/usePanier.js'
import { formatPrix } from '../utils/produit.js'

export default function PageDemande() {
  const { lignes, changerQuantite, changerTeinte, changerSouhait, retirer, total } = usePanier()

  if (lignes.length === 0) {
    return (
      <section className="etat contenu">
        <h1>Votre demande est vide</h1>
        <p>Ajoutez des pièces depuis la boutique pour recevoir un devis.</p>
        <Link to="/boutique">Découvrir la boutique</Link>
      </section>
    )
  }

  return (
    <section className="contenu section panier">
      <h1>Ma demande</h1>
      <ul className="panier__lignes">
        {lignes.map((ligne) => (
          <LigneArticlePanier
            key={ligne.produit_id}
            ligne={ligne}
            changerQuantite={changerQuantite}
            changerTeinte={changerTeinte}
            changerSouhait={changerSouhait}
            retirer={retirer}
          />
        ))}
      </ul>
      <p className="panier__total">Total indicatif : <strong>à partir de {formatPrix(total)}</strong>, hors livraison</p>
      <p className="infos__note">
        Rien n'est payé maintenant : vous recevez votre devis sous 48 h. Le prix final est fixé par
        l'artisane selon la finition et vos souhaits.
      </p>
      <Link to="/demande/envoi" className="bouton bouton--principal">Envoyer ma demande</Link>
    </section>
  )
}
