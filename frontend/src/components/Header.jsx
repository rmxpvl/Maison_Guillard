import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import Logo from './Logo.jsx'
import { useClientAuth } from '../hooks/useClientAuth.js'
import { usePanier } from '../hooks/usePanier.js'

// Scrolled further than this (px), the home header turns back to solid white.
const SEUIL_DEFILEMENT = 40

export default function Header() {
  const { nombreArticles } = usePanier()
  const { token: connecte, deconnexion } = useClientAuth()
  const navigate = useNavigate()
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
        <NavLink to="/actualites">Actualités</NavLink>
        <NavLink to="/qui-sommes-nous">Qui sommes-nous</NavLink>
        <NavLink to="/contact">Contact</NavLink>
      </nav>
      <div className="entete__actions">
        <Link to={connecte ? '/compte' : '/compte/connexion'} className="bouton bouton--discret">
          {connecte ? 'Mon compte' : 'Connexion'}
        </Link>
        {connecte && (
          <button
            type="button"
            className="bouton bouton--discret"
            onClick={() => { deconnexion(); navigate('/') }}
          >
            Se déconnecter
          </button>
        )}
        <Link
          to="/demande"
          className="bouton bouton--discret"
          aria-label={`Ma demande, ${nombreArticles} pièce${nombreArticles > 1 ? 's' : ''}`}
        >
          Ma demande
          {nombreArticles > 0 && <span className="pastille" aria-hidden="true">{nombreArticles}</span>}
        </Link>
      </div>
    </header>
  )
}
