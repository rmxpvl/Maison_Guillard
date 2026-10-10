import { Link } from 'react-router-dom'
import CarteProduit from '../components/CarteProduit.jsx'
import EtatChargement from '../components/EtatChargement.jsx'
import { getProduits } from '../api/produits.js'
import { useApi } from '../hooks/useApi.js'
import { piecesChoisies } from '../utils/produit.js'
import imageAccueil from '../assets/vitrine/accueil.webp'
import imageDetail from '../assets/vitrine/detail.webp'
import imageMatiere from '../assets/vitrine/matiere.webp'

export default function PageAccueil() {
  const produits = useApi(() => getProduits(), [])
  const pieces = piecesChoisies(produits.data ?? [], 3)
  const aucunePiece = produits.statut === 'ok' && pieces.length === 0

  return (
    <>
      <section className="hero">
        <img src={imageAccueil} alt="" className="hero__image" />
        <div className="hero__texte">
          <h1 className="hero__titre">Mobilier artisanal en bois massif</h1>
          <p className="hero__sous-titre">Pièces dessinées et fabriquées à la main</p>
          <Link to="/boutique" className="bouton">Découvrir la boutique</Link>
        </div>
      </section>

      <section className="contenu section deux-colonnes">
        <div className="texte-bloc">
          <p className="surtitre">Notre univers</p>
          <h2>Le bois, simplement</h2>
          <p>
            Des essences choisies pour leur veinage et leur solidité, des lignes épurées,
            des finitions naturelles. Chaque pièce est pensée pour le quotidien et
            fabriquée pour durer.
          </p>
        </div>
        <img src={imageMatiere} alt="" className="image image--portrait" />
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
        <img src={imageDetail} alt="" className="image image--carree" />
        <div className="texte-bloc">
          <p className="surtitre">Savoir-faire</p>
          <h2>Chaque pièce porte la trace de la main</h2>
          <p>
            Débit, assemblage, ponçage, finition : tout se fait à l'atelier, à l'unité ou en
            petite série, avec le temps qu'il faut.
          </p>
          <Link to="/qui-sommes-nous" className="lien-fleche">Qui sommes-nous</Link>
        </div>
      </section>
    </>
  )
}
