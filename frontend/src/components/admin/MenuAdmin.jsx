import { Link, useLocation, useSearchParams } from 'react-router-dom'
import Logo from '../Logo.jsx'
import { useAuth } from '../../hooks/useAuth.js'
import { useResumeAdmin } from '../../hooks/useResumeAdmin.js'
import { compterGroupes } from '../../utils/admin.js'

// Plain words for each part of the back-office, grouped by what the artisane is doing.
const GROUPES = [
  {
    titre: 'Au quotidien',
    liens: [
      { onglet: 'accueil', libelle: 'Aujourd’hui' },
      { onglet: 'demandes', libelle: 'Demandes et commandes' },
    ],
  },
  {
    titre: 'Mon site',
    liens: [
      { onglet: 'actualites', libelle: 'Actualités' },
      { onglet: 'pages', libelle: 'Pages du site' },
    ],
  },
  {
    titre: 'Mon catalogue',
    liens: [
      { onglet: 'produits', libelle: 'Produits' },
      { onglet: 'categories', libelle: 'Catégories' },
      { onglet: 'teintes', libelle: 'Finitions' },
    ],
  },
  { titre: 'Réglages', liens: [{ onglet: 'reglages', libelle: 'Informations du devis' }] },
]

export default function MenuAdmin() {
  const { deconnexion } = useAuth()
  const { demandes } = useResumeAdmin()
  const { pathname } = useLocation()
  const [params] = useSearchParams()
  const aFaire = compterGroupes(demandes).afaire

  // /admin/produits/12 (edit page) still belongs to « Produits ».
  const actif = pathname.startsWith('/admin/produits')
    ? 'produits'
    : pathname.startsWith('/admin/actualites')
      ? 'actualites'
      : (params.get('onglet') ?? 'accueil')

  return (
    <aside className="menu-admin">
      <Link to="/admin" className="menu-admin__marque" aria-label="Maison Guillard, gestion du site">
        <Logo />
        <span className="menu-admin__sous-titre">Gestion du site</span>
      </Link>

      <nav className="menu-admin__nav" aria-label="Gestion du site">
        {GROUPES.map((groupe) => (
          <div key={groupe.titre} className="menu-admin__groupe">
            <p className="menu-admin__titre-groupe">{groupe.titre}</p>
            {groupe.liens.map((lien) => (
              <Link
                key={lien.onglet}
                to={`/admin?onglet=${lien.onglet}`}
                className={`menu-admin__lien${actif === lien.onglet ? ' menu-admin__lien--actif' : ''}`}
                aria-current={actif === lien.onglet ? 'page' : undefined}
              >
                {lien.libelle}
                {lien.onglet === 'demandes' && aFaire > 0 && (
                  <span className="menu-admin__compteur" title={`${aFaire} à traiter`}>{aFaire}</span>
                )}
              </Link>
            ))}
          </div>
        ))}
      </nav>

      <div className="menu-admin__pied">
        <Link to="/" target="_blank" rel="noreferrer">Voir mon site</Link>
        <button type="button" className="lien-bouton" onClick={deconnexion}>Se déconnecter</button>
      </div>
    </aside>
  )
}
