import { Link } from 'react-router-dom'
import { useContenus } from '../hooks/useContenus.js'
import { UNIVERS } from '../utils/univers.js'

// The photo of each rayon can be changed by the artisane (« Pages du site » > Boutique).
const CLES_IMAGES = {
  meubles: 'boutique.meubles_image',
  ceramique: 'boutique.ceramique_image',
  papeterie: 'boutique.papeterie_image',
}

export default function PageBoutique() {
  const { image } = useContenus()
  return (
    <section className="contenu">
      <h1>Boutique</h1>
      <div className="univers-tuiles">
        {UNIVERS.map((u) => (
          <Link key={u.code} to={`/boutique/${u.code}`} className="univers-tuile">
            <img src={image(CLES_IMAGES[u.code])} alt="" className="univers-tuile__image" loading="lazy" />
            <span className="univers-tuile__nom">{u.nom}</span>
          </Link>
        ))}
      </div>
    </section>
  )
}
