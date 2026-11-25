import { LIENS_LEGAUX } from '../utils/legal.js'
import { Link, useLocation } from 'react-router-dom'
import Logo from './Logo.jsx'
import { COORDONNEES } from '../config/coordonnees.js'

// Simple line icons, drawn with currentColor like the logo.
function IconeInstagram() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true">
      <rect x="3" y="3" width="18" height="18" rx="5" />
      <circle cx="12" cy="12" r="4.2" />
      <circle cx="17.3" cy="6.7" r="1" fill="currentColor" stroke="none" />
    </svg>
  )
}

function IconePinterest() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" aria-hidden="true">
      <circle cx="12" cy="12" r="9.5" />
      <path d="M10.6 20.8 12.4 12.6 M9.6 13.9c-.9-2.9 1-6 4-6 2.4 0 3.8 1.6 3.8 3.6 0 2.5-1.4 4.6-3.5 4.6-1.3 0-2.1-.9-1.8-2.1" />
    </svg>
  )
}

// Compact footer: the pages of the menu are already in the header, so the footer only carries what
// is nowhere else: the workshop's contact details, its networks and the legal pages.
export default function Footer() {
  const { pathname } = useLocation()
  if (pathname.startsWith('/admin')) return null
  return (
    <footer className="pied">
      <div className="pied__interieur">
        <div className="pied__haut">
          <Link to="/" className="pied__logo" aria-label="Maison Guillard, accueil">
            <Logo />
          </Link>
          <address className="pied__coordonnees">
            <a href={`mailto:${COORDONNEES.email}`}>{COORDONNEES.email}</a>
            <a href={`tel:${COORDONNEES.telephone.replace(/\s/g, '')}`}>{COORDONNEES.telephone}</a>
            <span>{COORDONNEES.zone}</span>
          </address>
          <div className="pied__reseaux">
            <a href={COORDONNEES.reseaux.instagram} target="_blank" rel="noreferrer" aria-label="Instagram">
              <IconeInstagram />
            </a>
            <a href={COORDONNEES.reseaux.pinterest} target="_blank" rel="noreferrer" aria-label="Pinterest">
              <IconePinterest />
            </a>
          </div>
        </div>
        <div className="pied__bas">
          <nav aria-label="Informations légales">
            <ul className="pied__legal">
              {LIENS_LEGAUX.map((l) => <li key={l.to}><Link to={l.to}>{l.libelle}</Link></li>)}
            </ul>
          </nav>
          <p className="pied__copyright">© 2026 Maison Guillard</p>
        </div>
      </div>
    </footer>
  )
}
