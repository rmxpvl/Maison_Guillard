import { Fragment, useState } from 'react'
import { Link } from 'react-router-dom'
import EtatChargement from '../EtatChargement.jsx'
import { useApi } from '../../hooks/useApi.js'
import { useAuth } from '../../hooks/useAuth.js'
import { STATUTS_DEVIS, formatDate, libelleStatut } from '../../utils/admin.js'
import { messageErreurApi } from '../../utils/erreurs.js'

export default function OngletDevis() {
  const { appel } = useAuth()
  const [version, setVersion] = useState(0)
  const devis = useApi(() => appel('/devis'), [version])
  const [ouvert, setOuvert] = useState(null)
  const [erreur, setErreur] = useState(null)

  async function changerStatut(id, statut) {
    setErreur(null)
    try {
      await appel(`/devis/${id}/statut`, { method: 'PATCH', body: { statut } })
    } catch (err) {
      setErreur(messageErreurApi(err))
    }
    setVersion((v) => v + 1)
  }

  return (
    <div className="onglet">
      <h2>Demandes de devis</h2>
      {erreur && <p className="message-erreur" role="alert">{erreur}</p>}
      <EtatChargement
        statut={devis.statut}
        reessayer={devis.reessayer}
        vide={devis.data?.length === 0}
        messageVide="Aucune demande de devis pour le moment."
      >
        <table className="tableau">
          <thead>
            <tr>
              <th>N°</th><th>Date</th><th>Client</th><th>Produit</th><th>Statut</th>
              <th><span className="visuellement-cache">Détail</span></th>
            </tr>
          </thead>
          <tbody>
            {devis.data?.map((d) => (
              <Fragment key={d.id}>
                <tr>
                  <td>{d.id}</td>
                  <td>{formatDate(d.created_at)}</td>
                  <td>{d.nom_client}</td>
                  <td>{d.nom_produit ?? 'Sur mesure'}</td>
                  <td>{libelleStatut(STATUTS_DEVIS, d.statut)}</td>
                  <td>
                    <button
                      type="button"
                      className="lien-bouton"
                      aria-expanded={ouvert === d.id}
                      onClick={() => setOuvert(ouvert === d.id ? null : d.id)}
                    >
                      {ouvert === d.id ? 'Fermer' : 'Détail'}
                    </button>
                  </td>
                </tr>
                {ouvert === d.id && (
                  <tr className="tableau__detail">
                    <td colSpan={6}>
                      <div className="detail">
                        <dl className="detail__coordonnees">
                          <dt>E-mail</dt><dd><a href={`mailto:${d.email}`}>{d.email}</a></dd>
                          <dt>Téléphone</dt><dd>{d.telephone ?? 'Non renseigné'}</dd>
                          {d.produit_id && (
                            <>
                              <dt>Produit</dt>
                              <dd><Link to={`/produits/${d.produit_id}`}>{d.nom_produit}</Link></dd>
                            </>
                          )}
                        </dl>
                        <p className="detail__description">{d.description_projet}</p>
                        <label className="detail__statut">
                          Statut
                          <select value={d.statut} onChange={(e) => changerStatut(d.id, e.target.value)}>
                            {STATUTS_DEVIS.map(([valeur, libelle]) => (
                              <option key={valeur} value={valeur}>{libelle}</option>
                            ))}
                          </select>
                        </label>
                      </div>
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      </EtatChargement>
    </div>
  )
}
