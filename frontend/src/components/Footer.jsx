import { Link } from 'react-router-dom'
import Logo from './Logo.jsx'
import { COORDONNEES } from '../config/coordonnees.js'

export default function Footer() {
  return (
    <footer className="pied">
      <div className="pied__colonnes">
        <div>
          <Logo />
          <p className="pied__signature">Mobilier artisanal en bois massif.</p>
        </div>
        <nav className="pied__nav" aria-label="Pied de page">
          <Link to="/boutique">Boutique</Link>
          <Link to="/qui-sommes-nous">Qui sommes-nous</Link>
          <Link to="/contact">Contact</Link>
        </nav>
        <address className="pied__contact">
          <a href={`mailto:${COORDONNEES.email}`}>{COORDONNEES.email}</a>
          <span>{COORDONNEES.zone}</span>
        </address>
      </div>
      <p className="pied__copyright">© 2026 Maison Guillard</p>
    </footer>
  )
}
