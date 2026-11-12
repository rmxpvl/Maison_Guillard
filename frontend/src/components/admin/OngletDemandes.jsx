import { Fragment, useState } from 'react'
import EtatChargement from '../EtatChargement.jsx'
import EditeurDevis from './EditeurDevis.jsx'
import FilMessages from '../FilMessages.jsx'
import { useApi } from '../../hooks/useApi.js'
import { useAuth } from '../../hooks/useAuth.js'
import { STATUTS_DEMANDE, formatDate, libelleStatut, transitionsPossibles, urgenceDateLimite } from '../../utils/admin.js'
import { messageErreurApi } from '../../utils/erreurs.js'
import { formatPrix } from '../../utils/produit.js'

// Detail of one request: coordinates, pieces, quote editor, status buttons.
function DetailDemande({ id, apresChangement, changerStatut }) {
  const { appel } = useAuth()
  const [version, setVersion] = useState(0)
  const [erreurRemboursement, setErreurRemboursement] = useState(null)

  async function rembourser(demande) {
    const montant = formatPrix(demande.montant_paye)
    if (!window.confirm(`Rembourser la totalité de la commande n°${demande.id} (${montant}) ? Elle sera annulée.`)) return
    setErreurRemboursement(null)
    try {
      await appel(`/demandes/${demande.id}/rembourser`, { method: 'POST' })
      setVersion((v) => v + 1)
      apresChangement()
    } catch (err) {
      setErreurRemboursement(messageErreurApi(err))
    }
  }
  const demande = useApi(() => appel(`/demandes/${id}`), [appel, id, version])
  const types = useApi(() => appel('/messages-types'), [appel])

  return (
    <EtatChargement statut={demande.statut === 'ok' ? types.statut : demande.statut} reessayer={demande.reessayer}>
      {demande.data && (
        <div className="detail">
          <DetailCoordonnees d={demande.data} />
          <EditeurDevis
            key={`${demande.data.id}-${demande.data.version_devis}-${demande.data.statut}`}
            demande={demande.data}
            messagesTypes={types.data ?? []}
            apresEnvoi={() => { setVersion((v) => v + 1); apresChangement() }}
          />
          <FilMessages
            moi="artisane"
            charger={() => appel(`/demandes/${demande.data.id}/messages`)}
            envoyer={(texte) => appel(`/demandes/${demande.data.id}/messages`, { method: 'POST', body: { texte } })}
            titre="Messages avec le client"
          />
          {erreurRemboursement && <p className="message-erreur" role="alert">{erreurRemboursement}</p>}
          {['payee', 'en_fabrication'].includes(demande.data.statut) && (
            <div className="detail__statut">
              <button type="button" className="bouton" onClick={() => rembourser(demande.data)}>Rembourser</button>
            </div>
          )}
          {transitionsPossibles(demande.data.statut).length > 0 && (
            <div className="detail__statut">
              {transitionsPossibles(demande.data.statut).map((statut) => (
                <button
                  key={statut}
                  type="button"
                  className="bouton"
                  onClick={async () => { await changerStatut(demande.data.id, statut); setVersion((v) => v + 1) }}
                >
                  {{ annulee: 'Annuler la demande', en_fabrication: 'Passer en fabrication', expediee: 'Marquer expédiée', livree: 'Marquer livrée' }[statut]}
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </EtatChargement>
  )
}

function DetailCoordonnees({ d }) {
  return (
    <dl className="detail__coordonnees">
      <dt>E-mail</dt><dd><a href={`mailto:${d.email}`}>{d.email}</a></dd>
      <dt>Téléphone</dt><dd>{d.telephone ?? 'Non renseigné'}</dd>
      <dt>Adresse</dt><dd>{d.adresse ?? 'Non renseignée'}</dd>
      {d.message_client && (<><dt>Message</dt><dd>{d.message_client}</dd></>)}
      {d.description_projet && (<><dt>Projet</dt><dd>{d.description_projet}</dd></>)}
      {d.lignes.filter((l) => l.produit_id !== null).map((l) => (
        <Fragment key={l.id}>
          <dt>{l.libelle} × {l.quantite}</dt>
          <dd>{[l.teinte_nom, l.souhait && `« ${l.souhait} »`].filter(Boolean).join(' · ') || 'Aucune précision'}</dd>
        </Fragment>
      ))}
    </dl>
  )
}

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
              <th>N°</th><th>Date</th><th>Client</th><th>Pièces</th><th>Total indicatif</th><th>Statut</th><th>Date limite</th>
              <th><span className="visuellement-cache">Détail</span></th>
            </tr>
          </thead>
          <tbody>
            {demandes.data?.map((d) => (
              <Fragment key={d.id}>
                <tr>
                  <td>
                    {d.id}
                    {d.messages_non_lus > 0 && (
                      <span className="pastille" title="Messages du client non lus">{d.messages_non_lus}</span>
                    )}
                  </td>
                  <td>{formatDate(d.created_at)}</td>
                  <td>{d.nom_client}</td>
                  <td>{d.lignes.length === 0 ? 'Projet libre' : d.lignes.reduce((n, l) => n + l.quantite, 0)}</td>
                  <td>{d.lignes.length === 0 ? '—' : `dès ${formatPrix(d.total_indicatif)}`}</td>
                  <td>{libelleStatut(STATUTS_DEMANDE, d.statut)}</td>
                  <td className={`date-limite date-limite--${urgenceDateLimite(d.date_limite, d.statut) ?? 'ok'}`}>
                    {d.date_limite ? formatDate(d.date_limite) : '—'}
                  </td>
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
                    <td colSpan={8}>
                      <DetailDemande id={d.id} apresChangement={() => setVersion((v) => v + 1)} changerStatut={changerStatut} />
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
