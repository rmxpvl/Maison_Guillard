import { NavLink } from 'react-router-dom'

// « Tout » + the categories of one univers, as links under /boutique/<univers>.
export default function FiltreCategorie({ univers, categories }) {
  return (
    <nav className="filtre" aria-label="Filtrer par catégorie">
      <NavLink to={`/boutique/${univers}`} end className="puce">Tout</NavLink>
      {categories.map((c) => (
        <NavLink key={c.id} to={`/boutique/${univers}/${c.slug}`} className="puce">
          {c.nom}
        </NavLink>
      ))}
    </nav>
  )
}
