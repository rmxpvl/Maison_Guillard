import { useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import EtatChargement from '../../components/EtatChargement.jsx'
import { useApi } from '../../hooks/useApi.js'
import { useClientAuth } from '../../hooks/useClientAuth.js'
import { formatDate } from '../../utils/admin.js'
import { libelleStatutClient, totalAffiche } from '../../utils/compte.js'
import { messageErreurApi } from '../../utils/erreurs.js'
import { formatPrix } from '../../utils/produit.js'

// « Mon compte »: my requests with their status and unread messages. Each one opens its secret
// page (/devis/<jeton>), where the quote and the discussion thread live.
export default function PageCompte() {
  const { token, appel, deconnexion } = useClientAuth()
  const moi = useApi(() => (token ? appel('/clients/moi') : Promise.resolve(null)), [token, appel])
  const [suppression, setSuppression] = useState(false)
  const [motDePasse, setMotDePasse] = useState('')
  const [erreur, setErreur] = useState(null)

  if (!token) return <Navigate to="/compte/connexion" replace />

  async function supprimer(e) {
    e.preventDefault()
    setErreur(null)
    try {
      await appel('/clients/moi/supprimer', { method: 'POST', body: { mot_de_passe: motDePasse } })
      deconnexion()
    } catch (err) {
      setErreur(err.status === 401 ? 'Mot de passe incorrect.' : messageErreurApi(err))
    }
  }

  return (
    <section className="contenu section">
      <p className="surtitre">Mon compte</p>
      <h1>Mes demandes</h1>
      <EtatChargement
        statut={moi.statut}
        reessayer={moi.reessayer}
        vide={moi.data?.demandes.length === 0}
        messageVide="Vous n'avez pas encore envoyé de demande."
      >
        {moi.data && (
          <>
            <p className="infos__note">Connecté avec {moi.data.email}.</p>
            <ul className="detail__lignes">
              {moi.data.demandes.map((d) => {
                const total = totalAffiche(d)
                return (
                  <li key={d.id}>
                    <span>
                      <Link to={`/devis/${d.jeton}`}>
                        Demande n°{d.id}{d.numero_affiche && ` · devis ${d.numero_affiche}`}
                      </Link>
                      {' '}· {libelleStatutClient(d.statut)} · {formatDate(d.created_at)}
                      <br />
                      <span className="infos__note">{d.libelles.join(', ')}</span>
                      {d.messages_non_lus > 0 && (
                        <span className="pastille" role="status">
                          {' '}{d.messages_non_lus} message{d.messages_non_lus > 1 ? 's' : ''} non lu{d.messages_non_lus > 1 ? 's' : ''}
                        </span>
                      )}
                    </span>
                    <span>{total.indicatif ? 'dès ' : ''}{formatPrix(total.montant)}</span>
                  </li>
                )
              })}
            </ul>
          </>
        )}
      </EtatChargement>

      <div className="detail__statut">
        <Link to="/boutique" className="bouton">Découvrir la boutique</Link>
        <button type="button" className="bouton" onClick={deconnexion}>Se déconnecter</button>
      </div>

      <h2>Supprimer mon compte</h2>
      {!suppression ? (
        <button type="button" className="lien-bouton" onClick={() => setSuppression(true)}>Supprimer mon compte…</button>
      ) : (
        <form className="formulaire" onSubmit={supprimer}>
          <p className="infos__note">
            Votre compte est supprimé. L'atelier conserve vos demandes et commandes passées (historique de
            l'activité) ; vous ne pourrez plus les retrouver depuis un compte, seulement avec leur lien.
          </p>
          <label>
            Mot de passe, pour confirmer
            <input type="password" value={motDePasse} onChange={(e) => setMotDePasse(e.target.value)} required autoComplete="current-password" />
          </label>
          {erreur && <p className="message-erreur" role="alert">{erreur}</p>}
          <button type="submit" className="bouton">Supprimer définitivement</button>
        </form>
      )}
    </section>
  )
}
