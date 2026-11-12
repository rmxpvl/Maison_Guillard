import { useState } from 'react'
import { Link } from 'react-router-dom'
import EtatChargement from '../EtatChargement.jsx'
import { useApi } from '../../hooks/useApi.js'
import { useAuth } from '../../hooks/useAuth.js'
import { dateActu } from '../../utils/contenus.js'
import { messageErreurApi } from '../../utils/erreurs.js'

export default function OngletActualites() {
  const { appel } = useAuth()
  const [version, setVersion] = useState(0)
  const actualites = useApi(() => appel('/actualites/admin'), [appel, version])
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

  const basculer = (a) =>
    agir(
      () => appel(`/actualites/${a.id}`, { method: 'PUT', body: { publiee: !a.publiee } }),
      a.publiee ? `« ${a.titre} » n’est plus visible sur le site (brouillon).` : `« ${a.titre} » est publiée sur le site.`,
    )

  function supprimer(a) {
    if (!window.confirm(`Supprimer « ${a.titre} » et ses photos ? Cette action est définitive.`)) return
    return agir(() => appel(`/actualites/${a.id}`, { method: 'DELETE' }), `« ${a.titre} » a été supprimée.`)
  }

  return (
    <div className="page-admin">
      <header className="page-admin__entete">
        <div>
          <h1>Actualités</h1>
          <p className="page-admin__intro">
            Écrivez les nouvelles de votre atelier : une nouvelle pièce, un rendez-vous, les coulisses de la
            fabrication. Elles apparaissent sur la page « Actualités » de votre site, les plus récentes en premier.
          </p>
        </div>
        <Link to="/admin/actualites/nouveau" className="bouton bouton--principal">Écrire une actualité</Link>
      </header>

      {message && <p className="onglet__message" role="status">{message}</p>}
      {erreur && <p className="message-erreur" role="alert">{erreur}</p>}

      <EtatChargement
        statut={actualites.statut}
        reessayer={actualites.reessayer}
        vide={actualites.data?.length === 0}
        messageVide="Vous n’avez encore rien écrit. Cliquez sur « Écrire une actualité » pour commencer."
      >
        <ul className="produits">
          {actualites.data?.map((a) => (
            <li key={a.id} className={`produit${a.publiee ? '' : ' produit--masque'}`}>
              {a.photos[0]
                ? <img src={a.photos[0].url} alt="" className="produit__photo" />
                : <span className="produit__photo produit__photo--vide">Pas de photo</span>}
              <span className="produit__infos">
                <strong>{a.titre}</strong>
                <span>{dateActu(a.date_publication)}</span>
              </span>
              <span className={`badge ${a.publiee ? 'badge--ok' : 'badge--neutre'}`}>
                {a.publiee ? 'Publiée' : 'Brouillon'}
              </span>
              <span className="produit__actions">
                <Link to={`/admin/actualites/${a.id}`} className="bouton">Modifier</Link>
                <button type="button" className="bouton" onClick={() => basculer(a)}>
                  {a.publiee ? 'Dépublier' : 'Publier'}
                </button>
                <button type="button" className="lien-bouton lien-bouton--danger" onClick={() => supprimer(a)}>Supprimer</button>
              </span>
            </li>
          ))}
        </ul>
      </EtatChargement>
    </div>
  )
}
