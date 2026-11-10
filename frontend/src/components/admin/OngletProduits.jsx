import { useState } from 'react'
import { Link } from 'react-router-dom'
import EtatChargement from '../EtatChargement.jsx'
import { useApi } from '../../hooks/useApi.js'
import { useAuth } from '../../hooks/useAuth.js'
import { messageErreurApi } from '../../utils/erreurs.js'
import { formatPrix, photoPrincipale } from '../../utils/produit.js'

export default function OngletProduits() {
  const { appel } = useAuth()
  const [version, setVersion] = useState(0)
  const produits = useApi(() => appel('/produits/admin'), [appel, version])
  const [message, setMessage] = useState(null)
  const [erreur, setErreur] = useState(null)

  async function agir(requete, succes) {
    setMessage(null)
    setErreur(null)
    try {
      await requete()
      setMessage(succes)
      setVersion((v) => v + 1)
    } catch (err) {
      setErreur(messageErreurApi(err))
    }
  }

  const basculer = (p) =>
    agir(
      () => appel(`/produits/${p.id}`, { method: 'PUT', body: { visible: !p.visible } }),
      p.visible ? `« ${p.nom} » n’apparaît plus sur le site.` : `« ${p.nom} » est de nouveau visible sur le site.`,
    )

  function supprimer(p) {
    if (!window.confirm(`Supprimer « ${p.nom} » et ses photos ? Cette action est définitive.`)) return
    // 409 when a customer already requested it: the API says to hide it instead.
    return agir(() => appel(`/produits/${p.id}`, { method: 'DELETE' }), `« ${p.nom} » a été supprimé.`)
  }

  return (
    <div className="page-admin">
      <header className="page-admin__entete">
        <div>
          <h1>Produits</h1>
          <p className="page-admin__intro">
            Les pièces proposées sur votre site. Un produit masqué disparaît du site mais reste ici : vous pouvez le réafficher quand vous voulez.
          </p>
        </div>
        <Link to="/admin/produits/nouveau" className="bouton bouton--principal">Ajouter un produit</Link>
      </header>

      {message && <p className="onglet__message" role="status">{message}</p>}
      {erreur && <p className="message-erreur" role="alert">{erreur}</p>}

      <EtatChargement
        statut={produits.statut}
        reessayer={produits.reessayer}
        vide={produits.data?.length === 0}
        messageVide="Vous n’avez pas encore de produit. Cliquez sur « Ajouter un produit » pour commencer."
      >
        <ul className="produits">
          {produits.data?.map((p) => {
            const photo = photoPrincipale(p.photos)
            return (
              <li key={p.id} className={`produit${p.visible ? '' : ' produit--masque'}`}>
                {photo
                  ? <img src={photo.url} alt="" className="produit__photo" />
                  : <span className="produit__photo produit__photo--vide">Pas de photo</span>}
                <span className="produit__infos">
                  <strong>{p.nom}</strong>
                  <span>à partir de {formatPrix(p.prix)}</span>
                </span>
                <span className={`badge ${p.visible ? 'badge--ok' : 'badge--neutre'}`}>
                  {p.visible ? 'Visible sur le site' : 'Masqué'}
                </span>
                <span className="produit__actions">
                  <Link to={`/admin/produits/${p.id}`} className="bouton">Modifier</Link>
                  <button type="button" className="bouton" onClick={() => basculer(p)}>
                    {p.visible ? 'Masquer' : 'Afficher'}
                  </button>
                  <button type="button" className="lien-bouton lien-bouton--danger" onClick={() => supprimer(p)}>Supprimer</button>
                </span>
              </li>
            )
          })}
        </ul>
      </EtatChargement>
    </div>
  )
}
