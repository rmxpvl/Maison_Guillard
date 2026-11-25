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
      <div className="univers-tuiles">
        {UNIVERS.map((u) => (
          <Link key={u.code} to={`/boutique/${u.code}`} className="univers-tuile">
            <img src={imageOptimisee(image(CLE_IMAGE_UNIVERS[u.code]), LARGEURS.carte)} alt="" className="univers-tuile__image" loading="lazy" />
            <span className="univers-tuile__nom">{u.nom}</span>
          </Link>
        ))}
      </div>
    </section>
  )
}
