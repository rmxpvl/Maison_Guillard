import { Link } from 'react-router-dom'
import { useContenus } from '../hooks/useContenus.js'
import { CLE_IMAGE_UNIVERS, UNIVERS } from '../utils/univers.js'
import { useTitre } from '../hooks/useTitre.js'
import { imageOptimisee, LARGEURS } from '../utils/images.js'

export default function PageBoutique() {
  const { image } = useContenus()
  useTitre('Boutique', 'Meubles, céramique et papeterie fabriqués à la main par Maison Guillard, sur commande.')
  return (
    <section className="contenu">
      <div className="page-entete">
        <h1>Boutique</h1>
        <p className="introduction">Chaque pièce est fabriquée à la main, sur commande, à l’atelier. Choisissez un univers.</p>
      </div>
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
  )
}
