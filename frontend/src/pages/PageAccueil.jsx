import { Link } from 'react-router-dom'
import CarteProduit from '../components/CarteProduit.jsx'
import EtatChargement from '../components/EtatChargement.jsx'
import { getProduits } from '../api/produits.js'
import { useApi } from '../hooks/useApi.js'
import { useContenus } from '../hooks/useContenus.js'
import { paragraphes } from '../utils/contenus.js'
import { piecesChoisies } from '../utils/produit.js'

export default function PageAccueil() {
  const { texte, image } = useContenus()
  const produits = useApi(() => getProduits(), [])
  const pieces = piecesChoisies(produits.data ?? [], 3)
  const aucunePiece = produits.statut === 'ok' && pieces.length === 0

  return (
    <>
      <section className="hero">
        <img src={image('accueil.image')} alt="" className="hero__image" />
        <div className="hero__texte">
          <h1 className="hero__titre">{texte('accueil.titre')}</h1>
          <p className="hero__sous-titre">{texte('accueil.sous_titre')}</p>
          <Link to="/boutique" className="bouton">Découvrir la boutique</Link>
        </div>
      </section>

      <section className="contenu section deux-colonnes">
        <div className="texte-bloc">
          <p className="surtitre">Notre univers</p>
          <h2>{texte('accueil.univers_titre')}</h2>
          {paragraphes(texte('accueil.univers_texte')).map((p) => <p key={p}>{p}</p>)}
        </div>
        <img src={image('accueil.univers_image')} alt="" className="image image--portrait" />
      </section>

      {!aucunePiece && (
        <section className="contenu section">
          <div className="section__entete">
            <h2>Pièces choisies</h2>
            <Link to="/boutique" className="lien-fleche">Voir toute la boutique</Link>
          </div>
          <EtatChargement statut={produits.statut} reessayer={produits.reessayer}>
            <div className="grille">
              {pieces.map((p) => <CarteProduit key={p.id} produit={p} />)}
            </div>
          </EtatChargement>
        </section>
      )}

      <section className="contenu section deux-colonnes deux-colonnes--inverse">
        <img src={image('accueil.savoir_faire_image')} alt="" className="image image--carree" />
        <div className="texte-bloc">
          <p className="surtitre">Savoir-faire</p>
          <h2>{texte('accueil.savoir_faire_titre')}</h2>
          {paragraphes(texte('accueil.savoir_faire_texte')).map((p) => <p key={p}>{p}</p>)}
          <Link to="/qui-sommes-nous" className="lien-fleche">Qui sommes-nous</Link>
        </div>
      </section>
    </>
  )
}
