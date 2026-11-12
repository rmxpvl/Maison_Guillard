import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import BadgeStatut from './BadgeStatut.jsx'
import EditeurDevis from './EditeurDevis.jsx'
import SuiviEtapes from './SuiviEtapes.jsx'
import EtatChargement from '../EtatChargement.jsx'
import FilMessages from '../FilMessages.jsx'
import { useApi } from '../../hooks/useApi.js'
import { useAuth } from '../../hooks/useAuth.js'
import { useResumeAdmin } from '../../hooks/useResumeAdmin.js'
import {
  GROUPES_DEMANDES,
  STATUTS_DEMANDE,
  compterGroupes,
  filtrerDemandes,
  libelleStatut,
  nombreEtMot,
  prochaineEtape,
  tonStatut,
  urgenceDateLimite,
} from '../../utils/admin.js'
import { messageErreurApi } from '../../utils/erreurs.js'
import { formatPrix } from '../../utils/produit.js'

// The one action that moves an order forward, as a big button in the open request.
const ACTIONS = {
  payee: { statut: 'en_fabrication', libelle: 'Lancer la fabrication' },
  en_fabrication: {
    statut: 'expediee',
    libelle: 'Marquer comme expédiée',
    confirmation: 'Le client recevra un e-mail lui disant que sa commande est expédiée. Continuer ?',
  },
  expediee: { statut: 'livree', libelle: 'Marquer comme livrée' },
}

function jour(iso) {
  return new Date(iso).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })
}

function libelleFiltre(filtre) {
  const groupe = GROUPES_DEMANDES.find((g) => g.code === filtre)
  if (groupe) return groupe.libelle
  if (filtre === 'messages') return 'Messages non lus'
  if (filtre === 'toutes') return 'Toutes'
  return libelleStatut(STATUTS_DEMANDE, filtre)
}

function resumePieces(d) {
  if (d.lignes.length === 0) return 'Projet sur mesure'
  return d.lignes.map((l) => `${l.libelle}${l.quantite > 1 ? ` × ${l.quantite}` : ''}`).join(', ')
}

function Echeance({ d }) {
  if (!d.date_limite) return null
  const urgence = urgenceDateLimite(d.date_limite, d.statut)
  return (
    <span className={`echeance echeance--${urgence ?? 'ok'}`}>
      {urgence === 'depassee' ? 'En retard : ' : 'À livrer avant le '}
      {jour(d.date_limite)}
    </span>
  )
}

// Everything about one request, in the order the artisane needs it.
function DetailDemande({ id, recharger }) {
  const { appel } = useAuth()
  const [version, setVersion] = useState(0)
  const [retour, setRetour] = useState(null)
  const [erreur, setErreur] = useState(null)
  const demande = useApi(() => appel(`/demandes/${id}`), [appel, id, version])
  const types = useApi(() => appel('/messages-types'), [appel])

  async function agir(requete, succes, confirmation) {
    if (confirmation && !window.confirm(confirmation)) return
    setErreur(null)
    setRetour(null)
    try {
      await requete()
      setRetour(succes)
      setVersion((v) => v + 1)
      recharger()
    } catch (err) {
      setErreur(messageErreurApi(err))
    }
  }

  const changerStatut = (statut, succes, confirmation) =>
    agir(() => appel(`/demandes/${id}/statut`, { method: 'PATCH', body: { statut } }), succes, confirmation)

  return (
    <EtatChargement statut={demande.statut === 'ok' ? types.statut : demande.statut} reessayer={demande.reessayer}>
      {demande.data && (() => {
        const d = demande.data
        const action = ACTIONS[d.statut]
        const etape = prochaineEtape(d.statut)
        const remboursable = ['payee', 'en_fabrication'].includes(d.statut)
        return (
          <div className="detail-demande">
            <SuiviEtapes statut={d.statut} />

            {(etape || action) && (
              <div className="prochaine-etape">
                <p><strong>Prochaine étape :</strong> {etape}</p>
                {action && (
                  <button
                    type="button"
                    className="bouton bouton--principal"
                    onClick={() => changerStatut(action.statut, `Commande n°${d.id} : ${libelleStatut(STATUTS_DEMANDE, action.statut).toLowerCase()}.`, action.confirmation)}
                  >
                    {action.libelle}
                  </button>
                )}
              </div>
            )}
            {retour && <p className="onglet__message" role="status">{retour}</p>}
            {erreur && <p className="message-erreur" role="alert">{erreur}</p>}

            <div className="detail-demande__colonnes">
              <section>
                <h3>Le client</h3>
                <dl className="fiche">
                  <dt>Nom</dt><dd>{d.nom_client}</dd>
                  <dt>E-mail</dt><dd><a href={`mailto:${d.email}`}>{d.email}</a></dd>
                  <dt>Téléphone</dt><dd>{d.telephone ?? 'Non renseigné'}</dd>
                  <dt>Adresse de livraison</dt><dd>{d.adresse ?? 'Non renseignée'}</dd>
                  {d.message_client && (<><dt>Son message</dt><dd>{d.message_client}</dd></>)}
                </dl>
              </section>
              <section>
                <h3>Ce qu’il demande</h3>
                {d.description_projet && <p className="fiche__projet">{d.description_projet}</p>}
                <ul className="pieces">
                  {d.lignes.filter((l) => l.produit_id !== null).map((l) => (
                    <li key={l.id}>
                      <strong>{l.libelle}{l.quantite > 1 && ` × ${l.quantite}`}</strong>
                      {l.teinte_nom && <span>Finition : {l.teinte_nom}</span>}
                      {l.souhait && <span>Souhait : « {l.souhait} »</span>}
                    </li>
                  ))}
                </ul>
              </section>
            </div>

            <EditeurDevis
              key={`${d.id}-${d.version_devis}-${d.statut}`}
              demande={d}
              messagesTypes={types.data ?? []}
              apresEnvoi={() => { setVersion((v) => v + 1); recharger() }}
            />

            <FilMessages
              moi="artisane"
              charger={() => appel(`/demandes/${id}/messages`)}
              envoyer={async (texte) => {
                await appel(`/demandes/${id}/messages`, { method: 'POST', body: { texte } })
                recharger()
              }}
              titre="Messages avec le client"
            />

            {(remboursable || d.statut === 'nouvelle' || d.statut === 'devis_envoye') && (
              <div className="detail-demande__autres">
                <h3>Un souci avec cette commande ?</h3>
                {remboursable && (
                  <button
                    type="button"
                    className="bouton bouton--danger"
                    onClick={() => agir(
                      () => appel(`/demandes/${id}/rembourser`, { method: 'POST' }),
                      'Le client a été remboursé en totalité et la commande est annulée.',
                      `Rembourser la totalité de la commande n°${d.id} (${formatPrix(d.montant_paye)}) ? Elle sera annulée.`,
                    )}
                  >
                    Rembourser le client
                  </button>
                )}
                {(d.statut === 'nouvelle' || d.statut === 'devis_envoye') && (
                  <button
                    type="button"
                    className="bouton bouton--danger"
                    onClick={() => changerStatut('annulee', `La demande n°${d.id} est annulée.`, 'Annuler cette demande ? Le client ne pourra plus payer.')}
                  >
                    Annuler la demande
                  </button>
                )}
              </div>
            )}
          </div>
        )
      })()}
    </EtatChargement>
  )
}

export default function OngletDemandes() {
  const { statut, demandes, recharger, reessayer } = useResumeAdmin()
  const [params, setParams] = useSearchParams()
  const [ouverte, setOuverte] = useState(null)

  const compteurs = compterGroupes(demandes)
  // By default show what needs doing; if nothing does, show everything.
  const filtre = params.get('filtre') ?? (compteurs.afaire > 0 ? 'afaire' : 'toutes')
  const liste = filtrerDemandes(demandes, filtre)
  const filtreLibre = !GROUPES_DEMANDES.some((g) => g.code === filtre) && filtre !== 'toutes'

  const choisir = (code) => {
    setOuverte(null)
    setParams({ onglet: 'demandes', filtre: code })
  }

  return (
    <div className="page-admin">
      <header className="page-admin__entete">
        <div>
          <h1>Demandes et commandes</h1>
          <p className="page-admin__intro">
            Chaque client qui vous écrit apparaît ici. Cliquez sur une ligne pour voir le détail, envoyer un devis ou répondre.
          </p>
        </div>
      </header>

      <nav className="filtres" aria-label="Filtrer les demandes">
        {GROUPES_DEMANDES.map((g) => (
          <button
            key={g.code}
            type="button"
            className={`filtre${filtre === g.code ? ' filtre--actif' : ''}`}
            aria-pressed={filtre === g.code}
            onClick={() => choisir(g.code)}
          >
            {g.libelle} <span className="filtre__nombre">{compteurs[g.code]}</span>
          </button>
        ))}
        <button
          type="button"
          className={`filtre${filtre === 'toutes' ? ' filtre--actif' : ''}`}
          aria-pressed={filtre === 'toutes'}
          onClick={() => choisir('toutes')}
        >
          Toutes <span className="filtre__nombre">{compteurs.toutes}</span>
        </button>
      </nav>
      {filtreLibre && (
        <p className="page-admin__intro">
          Affichage : {libelleFiltre(filtre).toLowerCase()}.{' '}
          <button type="button" className="lien-bouton" onClick={() => choisir('toutes')}>Voir toutes les demandes</button>
        </p>
      )}

      <EtatChargement
        statut={statut}
        reessayer={reessayer}
        vide={liste.length === 0}
        messageVide={
          demandes.length === 0
            ? 'Aucune demande pour le moment. Dès qu’un client en enverra une depuis le site, elle apparaîtra ici.'
            : 'Aucune demande dans cette catégorie.'
        }
      >
        <ul className="demandes">
          {liste.map((d) => (
            <li key={d.id} className={`demande demande--${tonStatut(d.statut)}`}>
              <button
                type="button"
                className="demande__resume"
                aria-expanded={ouverte === d.id}
                onClick={() => setOuverte(ouverte === d.id ? null : d.id)}
              >
                <span className="demande__client">
                  <strong>{d.nom_client}</strong>
                  <span>{resumePieces(d)}</span>
                </span>
                <span className="demande__statut">
                  <BadgeStatut statut={d.statut} />
                  {d.messages_non_lus > 0 && (
                    <span className="badge badge--attention">{nombreEtMot(d.messages_non_lus, 'nouveau message', 'nouveaux messages')}</span>
                  )}
                </span>
                <span className="demande__montant">
                  {d.total_final != null
                    ? formatPrix(d.total_final)
                    : d.lignes.length === 0 ? '—' : `dès ${formatPrix(d.total_indicatif)}`}
                </span>
                <span className="demande__echeance"><Echeance d={d} /></span>
                <span className="demande__ouvrir">{ouverte === d.id ? 'Fermer' : 'Ouvrir'}</span>
              </button>
              {ouverte === d.id && (
                <div className="demande__detail">
                  <DetailDemande id={d.id} recharger={recharger} />
                </div>
              )}
            </li>
          ))}
        </ul>
      </EtatChargement>
    </div>
  )
}
