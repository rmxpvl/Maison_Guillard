import { Link } from 'react-router-dom'
import { useTitre } from '../hooks/useTitre.js'

export default function PageIntrouvable() {
  useTitre('Page introuvable', undefined, { noindex: true })
  return (
    <section className="etat contenu">
      <h1>Page introuvable</h1>
      <p>Ce que vous cherchez n'existe pas ou plus.</p>
      <p className="etat__liens">
        <Link to="/">Accueil</Link>
        <Link to="/boutique">Boutique</Link>
      </p>
    </section>
  )
}
