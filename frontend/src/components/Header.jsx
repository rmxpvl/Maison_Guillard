import { Link, NavLink } from 'react-router-dom'
import Logo from './Logo.jsx'

export default function Header() {
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
        <button type="button" className="bouton bouton--discret" disabled title="Bientôt disponible">
          Panier
        </button>
      </div>
    </header>
  )
}
