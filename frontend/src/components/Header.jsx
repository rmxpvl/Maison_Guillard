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
  // Small screens: the menu is folded behind a button. Remembering the page it was opened on
  // closes it by itself when the visitor goes elsewhere.
  const [ouvertSur, setOuvertSur] = useState(null)
  const menuOuvert = ouvertSur === pathname

  // Only the home page has a photo under the header: listen to scrolling there only.
  useEffect(() => {
    if (!surAccueil) return
    const mettreAJour = () => setDefile(window.scrollY > SEUIL_DEFILEMENT)
    mettreAJour()
    window.addEventListener('scroll', mettreAJour, { passive: true })
    return () => window.removeEventListener('scroll', mettreAJour)
  }, [surAccueil])

  useEffect(() => {
    if (!menuOuvert) return undefined
    const fermerAvecEchap = (e) => { if (e.key === 'Escape') setOuvertSur(null) }
    window.addEventListener('keydown', fermerAvecEchap)
    return () => window.removeEventListener('keydown', fermerAvecEchap)
  }, [menuOuvert])

  // The back-office has its own bar (BarreAdmin).
  if (pathname.startsWith('/admin')) return null

  const classes = ['entete']
  if (surAccueil) classes.push('entete--accueil')
  if (surAccueil && !defile && !menuOuvert) classes.push('entete--transparent')

  return (
    <header className={classes.join(' ')}>
      <Link to="/" className="entete__logo" aria-label="Maison Guillard, accueil">
        <Logo />
      </Link>
      <button
        type="button"
        className="entete__burger"
        aria-expanded={menuOuvert}
        aria-controls="menu-principal"
        aria-label={menuOuvert ? 'Fermer le menu' : 'Ouvrir le menu'}
        onClick={() => setOuvertSur(menuOuvert ? null : pathname)}
      >
        <span className="entete__burger-barres" aria-hidden="true" />
      </button>
      <div id="menu-principal" className={menuOuvert ? 'entete__menu entete__menu--ouvert' : 'entete__menu'}>
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
      </div>
    </header>
  )
}
