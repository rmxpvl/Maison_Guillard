import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation } from 'react-router-dom'
import Logo from './Logo.jsx'
import { usePanier } from '../hooks/usePanier.js'

// Scrolled further than this (px), the home header turns back to solid white.
const SEUIL_DEFILEMENT = 40

export default function Header() {
  const { nombreArticles } = usePanier()
  const { pathname } = useLocation()
  const surAccueil = pathname === '/'
  const [defile, setDefile] = useState(false)

  // Only the home page has a photo under the header: listen to scrolling there only.
  useEffect(() => {
    if (!surAccueil) return
    const mettreAJour = () => setDefile(window.scrollY > SEUIL_DEFILEMENT)
    mettreAJour()
    window.addEventListener('scroll', mettreAJour, { passive: true })
    return () => window.removeEventListener('scroll', mettreAJour)
  }, [surAccueil])

  // The back-office has its own bar (BarreAdmin).
  if (pathname.startsWith('/admin')) return null

  const classes = ['entete']
  if (surAccueil) classes.push('entete--accueil')
  if (surAccueil && !defile) classes.push('entete--transparent')

  return (
    <header className={classes.join(' ')}>
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
