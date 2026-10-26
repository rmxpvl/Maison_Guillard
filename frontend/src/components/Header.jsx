import { Link, NavLink, useLocation } from 'react-router-dom'
import Logo from './Logo.jsx'
import { usePanier } from '../hooks/usePanier.js'

export default function Header() {
  const { nombreArticles } = usePanier()
  const { pathname } = useLocation()
  // The back-office has its own bar (BarreAdmin).
  if (pathname.startsWith('/admin')) return null
  return (
    <header className="entete">
      <Link to="/" className="entete__logo" aria-label="Maison Guillard, accueil">
        <Logo />
      </Link>
      <nav className="entete__nav" aria-label="Navigation principale">
        <NavLink to="/boutique">Boutique</NavLink>
        <NavLink to="/qui-sommes-nous">Qui sommes-nous</NavLink>
        <NavLink to="/contact">Contact</NavLink>
      </nav>
      <div className="entete__actions">
        <Link
          to="/panier"
          className="bouton bouton--discret"
          aria-label={`Panier, ${nombreArticles} article${nombreArticles > 1 ? 's' : ''}`}
        >
          Panier
          {nombreArticles > 0 && <span className="pastille" aria-hidden="true">{nombreArticles}</span>}
        </Link>
      </div>
    </header>
  )
}
