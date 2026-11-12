import { Fragment, useState } from 'react'
import EtatChargement from '../EtatChargement.jsx'
import { useApi } from '../../hooks/useApi.js'
import { useAuth } from '../../hooks/useAuth.js'
import { STATUTS_DEMANDE, formatDate, libelleStatut, transitionsPossibles } from '../../utils/admin.js'
import { messageErreurApi } from '../../utils/erreurs.js'
import { formatPrix } from '../../utils/produit.js'

export default function OngletDemandes() {
  const { appel } = useAuth()
  const [filtre, setFiltre] = useState('')
  const [version, setVersion] = useState(0)
  const demandes = useApi(
    () => appel(`/demandes${filtre ? `?statut=${filtre}` : ''}`),
    [appel, filtre, version],
  )
  const [ouverte, setOuverte] = useState(null)
  const [erreur, setErreur] = useState(null)

  async function changerStatut(id, statut) {
    setErreur(null)
    try {
      await appel(`/demandes/${id}/statut`, { method: 'PATCH', body: { statut } })
    } catch (err) {
      setErreur(messageErreurApi(err))
    }
    setVersion((v) => v + 1)
  }

  return (
    <div className="onglet">
      <div className="onglet__entete">
        <h2>Demandes</h2>
        <label className="detail__statut">
          Statut
          <select value={filtre} onChange={(e) => setFiltre(e.target.value)}>
            <option value="">Tous</option>
            {STATUTS_DEMANDE.map(([valeur, libelle]) => <option key={valeur} value={valeur}>{libelle}</option>)}
          </select>
        </label>
      </div>
      {erreur && <p className="message-erreur" role="alert">{erreur}</p>}
      <EtatChargement
        statut={demandes.statut}
        reessayer={demandes.reessayer}
        vide={demandes.data?.length === 0}
        messageVide="Aucune demande pour le moment."
      >
        <table className="tableau">
          <thead>
            <tr>
              <th>N°</th><th>Date</th><th>Client</th><th>Pièces</th><th>Total indicatif</th><th>Statut</th>
              <th><span className="visuellement-cache">Détail</span></th>
            </tr>
          </thead>
          <tbody>
            {demandes.data?.map((d) => (
              <Fragment key={d.id}>
                <tr>
                  <td>{d.id}</td>
                  <td>{formatDate(d.created_at)}</td>
                  <td>{d.nom_client}</td>
                  <td>{d.lignes.length === 0 ? 'Projet libre' : d.lignes.reduce((n, l) => n + l.quantite, 0)}</td>
                  <td>{d.lignes.length === 0 ? '—' : `dès ${formatPrix(d.total_indicatif)}`}</td>
                  <td>{libelleStatut(STATUTS_DEMANDE, d.statut)}</td>
                  <td>
                    <button
                      type="button"
                      className="lien-bouton"
                      aria-expanded={ouverte === d.id}
                      onClick={() => setOuverte(ouverte === d.id ? null : d.id)}
                    >
                      {ouverte === d.id ? 'Fermer' : 'Détail'}
                    </button>
                  </td>
                </tr>
                {ouverte === d.id && (
                  <tr className="tableau__detail">
                    <td colSpan={7}>
                      <div className="detail">
                        <dl className="detail__coordonnees">
                          <dt>E-mail</dt><dd><a href={`mailto:${d.email}`}>{d.email}</a></dd>
                          <dt>Téléphone</dt><dd>{d.telephone ?? 'Non renseigné'}</dd>
                          <dt>Adresse</dt><dd>{d.adresse ?? 'Non renseignée'}</dd>
                          {d.message_client && (<><dt>Message</dt><dd>{d.message_client}</dd></>)}
                          {d.description_projet && (<><dt>Projet</dt><dd>{d.description_projet}</dd></>)}
                        </dl>
                        <ul className="detail__lignes">
                          {d.lignes.map((l) => (
                            <li key={l.id}>
                              <span>
                                {l.libelle} × {l.quantite}
                                {l.teinte_nom && ` · ${l.teinte_nom}`}
                                {l.souhait && ` · « ${l.souhait} »`}
                              </span>
                              <span>dès {formatPrix(Number(l.prix_indicatif) * l.quantite)}</span>
                            </li>
                          ))}
                        </ul>
                        {transitionsPossibles(d.statut).length > 0 && (
                          <div className="detail__statut">
                            {transitionsPossibles(d.statut).map((statut) => (
                              <button
                                key={statut}
                                type="button"
                                className="bouton"
                                onClick={() => changerStatut(d.id, statut)}
                              >
                                {{ annulee: 'Annuler la demande', en_fabrication: 'Passer en fabrication', expediee: 'Marquer expédiée', livree: 'Marquer livrée' }[statut]}
                              </button>
                            ))}
                          </div>
                        )}
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
