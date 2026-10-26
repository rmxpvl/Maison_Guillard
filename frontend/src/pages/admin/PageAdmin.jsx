import { useSearchParams } from 'react-router-dom'
import InterrupteurEmail from '../../components/admin/InterrupteurEmail.jsx'
import OngletCommandes from '../../components/admin/OngletCommandes.jsx'
import OngletDevis from '../../components/admin/OngletDevis.jsx'
import OngletProduits from '../../components/admin/OngletProduits.jsx'

const ONGLETS = [
  ['produits', 'Produits'],
  ['commandes', 'Commandes'],
  ['devis', 'Devis'],
]

// The current tab lives in the URL (?onglet=…): reload and back button keep it.
export default function PageAdmin() {
  const [params, setParams] = useSearchParams()
  const demande = params.get('onglet')
  const onglet = ONGLETS.some(([code]) => code === demande) ? demande : 'produits'

  return (
    <section className="contenu admin">
      <InterrupteurEmail />
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
      {onglet === 'commandes' && <OngletCommandes />}
      {onglet === 'devis' && <OngletDevis />}
    </section>
  )
}
