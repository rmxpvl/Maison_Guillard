import { Link } from 'react-router-dom'

export default function PageIntrouvable() {
  return (
    <section className="etat contenu">
      <h1>Page introuvable</h1>
      <p>Ce que vous cherchez n'existe pas ou plus.</p>
      <Link to="/boutique">Retour à la boutique</Link>
    </section>
  )
}
