import { Link, useParams } from 'react-router-dom'
import EtatChargement from '../components/EtatChargement.jsx'
import GaleriePhotos from '../components/GaleriePhotos.jsx'
import InfosProduit from '../components/InfosProduit.jsx'
import PageIntrouvable from './PageIntrouvable.jsx'
import { getProduit } from '../api/produits.js'
import { useApi } from '../hooks/useApi.js'
import { parseIdProduit } from '../utils/produit.js'

export default function PageFicheProduit() {
  const { id } = useParams()
  const produitId = parseIdProduit(id)
  const produit = useApi(
    () => (produitId === null ? Promise.resolve(null) : getProduit(produitId)),
    [produitId],
  )

  if (produitId === null || produit.erreur?.status === 404) {
    return <PageIntrouvable />
  }

  return (
    <section className="contenu">
      <Link to="/boutique" className="retour">← Retour à la boutique</Link>
      <EtatChargement statut={produit.statut} reessayer={produit.reessayer}>
        {produit.data && (
          <article className="fiche">
            {/* key resets the selected thumbnail when navigating to another produit */}
            <GaleriePhotos key={produit.data.id} photos={produit.data.photos} nom={produit.data.nom} />
            <InfosProduit produit={produit.data} />
          </article>
        )}
      </EtatChargement>
    </section>
  )
}
