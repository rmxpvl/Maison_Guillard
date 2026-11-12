import { Link } from 'react-router-dom'
import { UNIVERS } from '../utils/univers.js'
import imageMeubles from '../assets/vitrine/matiere.webp'
import imageCeramique from '../assets/vitrine/ceramique.webp'
import imagePapeterie from '../assets/vitrine/univers.webp'

// Photos of the three univers (Meubles and Papeterie are still provisional).
const IMAGES = { meubles: imageMeubles, ceramique: imageCeramique, papeterie: imagePapeterie }

export default function PageBoutique() {
  return (
    <section className="contenu">
      <h1>Boutique</h1>
      <div className="univers-tuiles">
        {UNIVERS.map((u) => (
          <Link key={u.code} to={`/boutique/${u.code}`} className="univers-tuile">
            <img src={IMAGES[u.code]} alt="" className="univers-tuile__image" loading="lazy" />
            <span className="univers-tuile__nom">{u.nom}</span>
          </Link>
        ))}
      </div>
    </section>
  )
}
