import { Link } from 'react-router-dom'
import { dateActu, extrait } from '../utils/contenus.js'

// A post in a list (the Actualités page and the home page): cover photo, date, title, start of the text.
export default function CarteActualite({ actualite: a }) {
  return (
    <Link to={`/actualites/${a.slug}`} className="actu-carte">
      {a.photos[0]
        ? <img src={a.photos[0].url} alt="" className="actu-carte__photo" loading="lazy" />
        : <span className="actu-carte__photo actu-carte__photo--vide" aria-hidden="true" />}
      <span className="actu-carte__date">{dateActu(a.date_publication)}</span>
      <h2 className="actu-carte__titre">{a.titre}</h2>
      <span className="actu-carte__extrait">{extrait(a.contenu, 160)}</span>
    </Link>
  )
}
