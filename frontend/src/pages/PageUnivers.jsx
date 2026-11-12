import { useOutletContext, useParams } from 'react-router-dom'
import CarteProduit from '../components/CarteProduit.jsx'
import EtatChargement from '../components/EtatChargement.jsx'
import FiltreCategorie from '../components/FiltreCategorie.jsx'
import PageIntrouvable from './PageIntrouvable.jsx'
import { getProduits } from '../api/produits.js'
import { useApi } from '../hooks/useApi.js'
import { avecPhotosDabord } from '../utils/produit.js'
import { categoriesDeLUnivers, messageUniversVide, universParCode } from '../utils/univers.js'

// /boutique/:univers and /boutique/:univers/:categorie
export default function PageUnivers() {
  const { univers: code, categorie: slug } = useParams()
  const { categories } = useOutletContext()

  const univers = universParCode(code)
  const categoriesUnivers = categoriesDeLUnivers(categories.data ?? [], code)
  const categorie = slug ? categoriesUnivers.find((c) => c.slug === slug) : null
  const categorieId = categorie?.id ?? null

  const produits = useApi(
    () => (univers ? getProduits({ univers: code, categorie: categorieId }) : Promise.resolve([])),
    [code, categorieId],
  )

  if (!univers) return <PageIntrouvable />
  // A slug unknown to this univers (typed by hand, renamed or moved category) is a 404.
  if (slug && categories.statut === 'ok' && !categorie) return <PageIntrouvable />

  // With a slug, the category list must be loaded before the product list means anything.
  const enCours = slug && categories.statut !== 'ok' ? categories : produits

  return (
    <section className="contenu">
      <h1>{categorie ? categorie.nom : univers.nom}</h1>
      <div className="barre-filtres">
        <FiltreCategorie univers={code} categories={categoriesUnivers} />
      </div>
      <EtatChargement
        statut={enCours.statut}
        reessayer={enCours.reessayer}
        vide={produits.data?.length === 0}
        messageVide={categorie ? 'Aucun produit dans cette catégorie.' : messageUniversVide}
      >
        <div className="grille">
          {avecPhotosDabord(produits.data ?? []).map((p) => <CarteProduit key={p.id} produit={p} />)}
        </div>
      </EtatChargement>
    </section>
  )
}
