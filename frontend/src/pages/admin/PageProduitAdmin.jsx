import { useState } from 'react'
import { Link, useNavigate, useOutletContext, useParams } from 'react-router-dom'
import EtatChargement from '../../components/EtatChargement.jsx'
import FormulaireProduit from '../../components/admin/FormulaireProduit.jsx'
import PhotosProduit from '../../components/admin/PhotosProduit.jsx'
import { getProduit } from '../../api/produits.js'
import { useApi } from '../../hooks/useApi.js'
import { useAuth } from '../../hooks/useAuth.js'
import { PRODUIT_VIDE, formulaireDepuisProduit, produitPourApi } from '../../utils/admin.js'
import { messageErreurApi } from '../../utils/erreurs.js'
import { parseIdProduit } from '../../utils/produit.js'

// /admin/produits/nouveau (no :id) creates a product; /admin/produits/:id edits one.
export default function PageProduitAdmin() {
  const { id } = useParams()
  const creation = id === undefined
  const produitId = creation ? null : parseIdProduit(id)
  const { categories } = useOutletContext()
  const { appel } = useAuth()
  const navigate = useNavigate()
  const [version, setVersion] = useState(0)
  const [message, setMessage] = useState(null)
  const produit = useApi(
    () => (produitId === null ? Promise.resolve(null) : getProduit(produitId)),
    [produitId, version],
  )

  if (!creation && (produitId === null || produit.erreur?.status === 404)) {
    return (
      <section className="contenu etat">
        <h1>Produit introuvable</h1>
        <Link to="/admin">Retour à l'administration</Link>
      </section>
    )
  }

  async function enregistrer(champs) {
    setMessage(null)
    try {
      if (creation) {
        const cree = await appel('/produits', { method: 'POST', body: produitPourApi(champs) })
        // Go to the edit page so photos can be added right away.
        navigate(`/admin/produits/${cree.id}`, { replace: true })
      } else {
        await appel(`/produits/${produitId}`, { method: 'PUT', body: produitPourApi(champs) })
        setMessage('Modifications enregistrées.')
        setVersion((v) => v + 1)
      }
    } catch (err) {
      setMessage(messageErreurApi(err))
    }
  }

  const pret = categories.statut === 'ok' && (creation || produit.statut === 'ok')

  return (
    <section className="contenu admin produit-admin">
      <Link to="/admin" className="retour">← Retour aux produits</Link>
      <h1>{creation ? 'Nouveau produit' : produit.data?.nom ?? 'Produit'}</h1>
      {message && <p className="onglet__message" role="status">{message}</p>}
      <EtatChargement
        statut={pret ? 'ok' : categories.statut === 'erreur' || produit.statut === 'erreur' ? 'erreur' : 'chargement'}
        reessayer={categories.statut === 'erreur' ? categories.reessayer : produit.reessayer}
      >
        {pret && (
          <div className="produit-admin__colonnes">
            {/* key: start from the saved values once the product is loaded */}
            <FormulaireProduit
              key={produit.data?.id ?? 'nouveau'}
              initial={creation ? PRODUIT_VIDE : formulaireDepuisProduit(produit.data)}
              categories={categories.data}
              libelleBouton={creation ? 'Créer le produit' : 'Enregistrer'}
              enregistrer={enregistrer}
            />
            {!creation && (
              <PhotosProduit produit={produit.data} apresChangement={() => setVersion((v) => v + 1)} />
            )}
          </div>
        )}
      </EtatChargement>
    </section>
  )
}
