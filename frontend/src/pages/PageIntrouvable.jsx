import { Link } from 'react-router-dom'

export default function PageIntrouvable() {
  return (
    <section className="etat">
      <h1>Page introuvable</h1>
      <p>Ce que vous cherchez n'existe pas ou plus.</p>
      <Link to="/">Retour au catalogue</Link>
    </section>
  )
}
