import { Link, NavLink } from 'react-router-dom'

export default function Header({ categories }) {
  return (
    <header className="entete">
      <Link to="/" className="entete__logo">Maison Guillard</Link>
      <nav className="entete__nav" aria-label="Catégories">
        <NavLink to="/" end>Catalogue</NavLink>
        {categories.map((c) => (
          <NavLink key={c.id} to={`/categorie/${c.slug}`}>{c.nom}</NavLink>
        ))}
      </nav>
      <div className="entete__actions">
        <button type="button" className="bouton" disabled title="Bientôt disponible">Projet sur mesure</button>
        <button type="button" className="bouton" disabled title="Bientôt disponible">Panier</button>
      </div>
    </header>
  )
}
