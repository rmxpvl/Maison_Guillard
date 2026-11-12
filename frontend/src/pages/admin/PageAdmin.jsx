import { useSearchParams } from 'react-router-dom'
import OngletCategories from '../../components/admin/OngletCategories.jsx'
import OngletDemandes from '../../components/admin/OngletDemandes.jsx'
import OngletProduits from '../../components/admin/OngletProduits.jsx'
import OngletTeintes from '../../components/admin/OngletTeintes.jsx'

const ONGLETS = [
  ['produits', 'Produits'],
  ['categories', 'Catégories'],
  ['teintes', 'Teintes'],
  ['demandes', 'Demandes'],
]

// The current tab lives in the URL (?onglet=…): reload and back button keep it.
export default function PageAdmin() {
  const [params, setParams] = useSearchParams()
  const demande = params.get('onglet')
  const onglet = ONGLETS.some(([code]) => code === demande) ? demande : 'produits'

  return (
    <section className="contenu admin">
      <nav className="onglets" aria-label="Sections de l'administration">
        {ONGLETS.map(([code, libelle]) => (
          <button
            key={code}
            type="button"
            className={`onglets__bouton${code === onglet ? ' onglets__bouton--actif' : ''}`}
            aria-current={code === onglet ? 'page' : undefined}
            onClick={() => setParams({ onglet: code })}
          >
            {libelle}
          </button>
        ))}
      </nav>
      {onglet === 'produits' && <OngletProduits />}
      {onglet === 'categories' && <OngletCategories />}
      {onglet === 'teintes' && <OngletTeintes />}
      {onglet === 'demandes' && <OngletDemandes />}
    </section>
  )
}
