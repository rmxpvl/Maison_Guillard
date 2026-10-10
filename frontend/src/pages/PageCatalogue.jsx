import { useOutletContext, useParams, useSearchParams } from 'react-router-dom'
import CarteProduit from '../components/CarteProduit.jsx'
import EtatChargement from '../components/EtatChargement.jsx'
import FiltreCategorie from '../components/FiltreCategorie.jsx'
import FiltreDisponibilite from '../components/FiltreDisponibilite.jsx'
import PageIntrouvable from './PageIntrouvable.jsx'
import { getProduits } from '../api/produits.js'
import { useApi } from '../hooks/useApi.js'
import { disponibiliteValide } from '../utils/produit.js'

export default function PageCatalogue() {
  const { slug } = useParams()
  const [params] = useSearchParams()
  const { categories } = useOutletContext()

  const disponibilite = disponibiliteValide(params.get('disponibilite'))
  const categorie = slug ? categories.data?.find((c) => c.slug === slug) : null
  const categorieId = categorie?.id ?? null

  const produits = useApi(
    () => getProduits({ categorie: categorieId, disponibilite }),
    [categorieId, disponibilite],
  )

  if (slug && categories.statut === 'ok' && !categorie) {
    return <PageIntrouvable />
  }

  // With a slug, the category list must be loaded before the product list means anything.
  const enCours = slug && categories.statut !== 'ok' ? categories : produits

  return (
    <section>
      <h1>{categorie ? categorie.nom : 'Catalogue'}</h1>
      <div className="barre-filtres">
        <FiltreCategorie categories={categories.data ?? []} />
        <FiltreDisponibilite />
      </div>
      <EtatChargement
        statut={enCours.statut}
        reessayer={enCours.reessayer}
        vide={produits.data?.length === 0}
        messageVide="Aucun produit ne correspond à ces critères."
      >
        <div className="grille">
          {produits.data?.map((p) => <CarteProduit key={p.id} produit={p} />)}
        </div>
      </EtatChargement>
    </section>
  )
}
