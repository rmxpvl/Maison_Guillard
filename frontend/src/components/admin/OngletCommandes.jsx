import { Fragment, useState } from 'react'
import EtatChargement from '../EtatChargement.jsx'
import { useApi } from '../../hooks/useApi.js'
import { useAuth } from '../../hooks/useAuth.js'
import { STATUTS_COMMANDE, formatDate, libelleStatut } from '../../utils/admin.js'
import { messageErreurApi } from '../../utils/erreurs.js'
import { formatPrix } from '../../utils/produit.js'

export default function OngletCommandes() {
  const { appel } = useAuth()
  const [version, setVersion] = useState(0)
  const commandes = useApi(() => appel('/commandes'), [version])
  const [ouverte, setOuverte] = useState(null)
  const [erreur, setErreur] = useState(null)

  async function changerStatut(id, statut) {
    setErreur(null)
    try {
      await appel(`/commandes/${id}/statut`, { method: 'PATCH', body: { statut } })
    } catch (err) {
      setErreur(messageErreurApi(err))
    }
    setVersion((v) => v + 1) // reload: shows the saved status, or drops a deleted order
  }

  return (
    <div className="onglet">
      <h2>Commandes</h2>
      {erreur && <p className="message-erreur" role="alert">{erreur}</p>}
      <EtatChargement
        statut={commandes.statut}
        reessayer={commandes.reessayer}
        vide={commandes.data?.length === 0}
        messageVide="Aucune commande pour le moment."
      >
        <table className="tableau">
          <thead>
            <tr>
              <th>N°</th><th>Date</th><th>Client</th><th>Total</th><th>Statut</th>
              <th><span className="visuellement-cache">Détail</span></th>
            </tr>
          </thead>
          <tbody>
            {commandes.data?.map((c) => (
              <Fragment key={c.id}>
                <tr>
                  <td>{c.id}</td>
                  <td>{formatDate(c.created_at)}</td>
                  <td>{c.nom_client}</td>
                  <td>{formatPrix(c.total)}</td>
                  <td>{libelleStatut(STATUTS_COMMANDE, c.statut)}</td>
                  <td>
                    <button
                      type="button"
                      className="lien-bouton"
                      aria-expanded={ouverte === c.id}
                      onClick={() => setOuverte(ouverte === c.id ? null : c.id)}
                    >
                      {ouverte === c.id ? 'Fermer' : 'Détail'}
                    </button>
                  </td>
                </tr>
                {ouverte === c.id && (
                  <tr className="tableau__detail">
                    <td colSpan={6}>
                      <div className="detail">
                        <dl className="detail__coordonnees">
                          <dt>E-mail</dt><dd><a href={`mailto:${c.email}`}>{c.email}</a></dd>
                          <dt>Téléphone</dt><dd>{c.telephone ?? 'Non renseigné'}</dd>
                          <dt>Adresse</dt><dd>{c.adresse}</dd>
                        </dl>
                        <ul className="detail__lignes">
                          {c.lignes.map((l) => (
                            <li key={l.id}>
                              <span>{l.nom_produit ?? `Produit n°${l.produit_id}`} × {l.quantite}</span>
                              <span>{formatPrix(Number(l.prix_unitaire_snapshot) * l.quantite)}</span>
                            </li>
                          ))}
                        </ul>
                        <label className="detail__statut">
                          Statut
                          <select value={c.statut} onChange={(e) => changerStatut(c.id, e.target.value)}>
                            {STATUTS_COMMANDE.map(([valeur, libelle]) => (
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
