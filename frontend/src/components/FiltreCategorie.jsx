import { NavLink, useLocation } from 'react-router-dom'

// Keeps the current ?disponibilite= when switching category.
export default function FiltreCategorie({ categories }) {
  const { search } = useLocation()
  return (
    <nav className="filtre" aria-label="Filtrer par catégorie">
      <NavLink to={{ pathname: '/', search }} end className="puce">Toutes</NavLink>
      {categories.map((c) => (
        <NavLink key={c.id} to={{ pathname: `/categorie/${c.slug}`, search }} className="puce">
          {c.nom}
        </NavLink>
      ))}
    </nav>
  )
}
