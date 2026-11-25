import { Link } from 'react-router-dom'
import CarteActualite from '../components/CarteActualite.jsx'
import CarteProduit from '../components/CarteProduit.jsx'
import EtatChargement from '../components/EtatChargement.jsx'
import { getActualites } from '../api/actualites.js'
import { getProduits } from '../api/produits.js'
import { useApi } from '../hooks/useApi.js'
import { useContenus } from '../hooks/useContenus.js'
import { dernieres, paragraphes } from '../utils/contenus.js'
import { piecesChoisies } from '../utils/produit.js'
import { CLE_IMAGE_UNIVERS, UNIVERS } from '../utils/univers.js'
import { useTitre } from '../hooks/useTitre.js'
import { imageOptimisee, LARGEURS } from '../utils/images.js'

// Home page, editorial layout: full-screen photo, centred text blocks in a serif, portrait photos
// with their caption centred underneath.
export default function PageAccueil() {
  useTitre()
  const { texte, image } = useContenus()
  const produits = useApi(() => getProduits(), [])
  const actualites = useApi(getActualites, [])
  const pieces = piecesChoisies(produits.data ?? [], 4)
  const actus = dernieres(actualites.data, 3)
  const aucunePiece = produits.statut === 'ok' && pieces.length === 0

  return (
    <div className="accueil">
      <section className="hero">
        <img src={imageOptimisee(image('accueil.image'), LARGEURS.grande)} alt="" className="hero__image" fetchPriority="high" />
        <div className="hero__texte">
          <h1 className="hero__titre">{texte('accueil.titre')}</h1>
          <p className="hero__sous-titre">{texte('accueil.sous_titre')}</p>
          <Link to="/boutique" className="lien-capitales">Découvrir la boutique</Link>
        </div>
      </section>

      <section className="contenu section bloc-centre">
        <p className="surtitre">Notre univers</p>
        <h2 className="titre-capitales">{texte('accueil.univers_titre')}</h2>
        {paragraphes(texte('accueil.univers_texte')).map((p) => <p key={p} className="texte-serif">{p}</p>)}
        <Link to="/qui-sommes-nous" className="lien-capitales">Découvrir l’atelier</Link>
      </section>

      <section className="contenu section">
        <ul className="vignettes">
          {UNIVERS.map((u) => (
            <li key={u.code}>
              <Link to={`/boutique/${u.code}`} className="vignette">
                <img src={imageOptimisee(image(CLE_IMAGE_UNIVERS[u.code]), LARGEURS.carte)} alt="" className="vignette__image" loading="lazy" />
                <span className="vignette__legende">{u.nom}</span>
              </Link>
            </li>
          ))}
        </ul>
      </section>

      {!aucunePiece && (
        <section className="contenu section">
          <div className="bloc-centre bloc-centre--court">
            <h2 className="titre-capitales">Pièces choisies</h2>
          </div>
          <EtatChargement statut={produits.statut} reessayer={produits.reessayer}>
            <div className="grille grille--accueil">
              {pieces.map((p) => <CarteProduit key={p.id} produit={p} />)}
            </div>
          </EtatChargement>
          <p className="bloc-centre bloc-centre--court"><Link to="/boutique" className="lien-capitales">Voir toute la boutique</Link></p>
        </section>
      )}

      <section className="contenu section deux-colonnes deux-colonnes--inverse">
        <img src={imageOptimisee(image('accueil.savoir_faire_image'), LARGEURS.moyenne)} alt="" className="image image--portrait" loading="lazy" />
        <div className="texte-bloc">
          <p className="surtitre">Savoir-faire</p>
          <h2 className="titre-capitales">{texte('accueil.savoir_faire_titre')}</h2>
          {paragraphes(texte('accueil.savoir_faire_texte')).map((p) => <p key={p} className="texte-serif">{p}</p>)}
          <Link to="/qui-sommes-nous" className="lien-capitales">Qui sommes-nous</Link>
        </div>
      </section>

      {/* Shown only when the artisane has published something: nothing (not even a title) otherwise. */}
      {actus.length > 0 && (
        <section className="contenu section">
          <div className="bloc-centre bloc-centre--court">
            <h2 className="titre-capitales">Dernières actualités</h2>
          </div>
          <ul className="actus">
            {actus.map((a) => <li key={a.id}><CarteActualite actualite={a} /></li>)}
          </ul>
          <p className="bloc-centre bloc-centre--court"><Link to="/actualites" className="lien-capitales">Toutes les actualités</Link></p>
        </section>
      )}
    </div>
  )
}
