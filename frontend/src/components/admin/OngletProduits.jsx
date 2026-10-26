import { useState } from 'react'
import { Link } from 'react-router-dom'
import EtatChargement from '../EtatChargement.jsx'
import { getProduits } from '../../api/produits.js'
import { useApi } from '../../hooks/useApi.js'
import { useAuth } from '../../hooks/useAuth.js'
import { messageErreurApi } from '../../utils/erreurs.js'
import { formatPrix, libelleDisponibilite, photoPrincipale } from '../../utils/produit.js'

export default function OngletProduits() {
  const { appel } = useAuth()
  const [version, setVersion] = useState(0)
  const produits = useApi(getProduits, [version])
  const [message, setMessage] = useState(null)

  async function supprimer(produit) {
    if (!window.confirm(`Supprimer « ${produit.nom} » et ses photos ?`)) return
    try {
      await appel(`/produits/${produit.id}`, { method: 'DELETE' })
      setMessage(`« ${produit.nom} » a été supprimé.`)
      setVersion((v) => v + 1)
    } catch (err) {
      // 409 when the product is in an order: the API says to switch it to « rupture ».
      setMessage(messageErreurApi(err))
    }
  }

  return (
    <div className="onglet">
      <div className="onglet__entete">
        <h2>Produits</h2>
        <Link to="/admin/produits/nouveau" className="bouton bouton--principal">Nouveau produit</Link>
      </div>
      {message && <p className="onglet__message" role="status">{message}</p>}
      <EtatChargement statut={produits.statut} reessayer={produits.reessayer}>
        <table className="tableau">
          <thead>
            <tr>
              <th>Photo</th><th>Nom</th><th>Prix</th><th>Disponibilité</th>
              <th><span className="visuellement-cache">Actions</span></th>
            </tr>
          </thead>
          <tbody>
            {produits.data?.map((p) => {
              const photo = photoPrincipale(p.photos)
              return (
                <tr key={p.id}>
                  <td>
                    {photo ? <img src={photo.url} alt="" className="tableau__vignette" /> : <span className="tableau__vide">—</span>}
                  </td>
                  <td>{p.nom}</td>
                  <td>{formatPrix(p.prix)}</td>
                  <td>{libelleDisponibilite(p.disponibilite)}</td>
                  <td className="tableau__actions">
                    <Link to={`/admin/produits/${p.id}`}>Modifier</Link>
                    <button type="button" className="lien-bouton" onClick={() => supprimer(p)}>Supprimer</button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </EtatChargement>
    </div>
  )
}
