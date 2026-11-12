import { useState } from 'react'
import EtatChargement from './EtatChargement.jsx'
import { useApi } from '../hooks/useApi.js'
import { formatDate } from '../utils/admin.js'
import { messageErreurApi } from '../utils/erreurs.js'

// Discussion thread of a request, used on both sides. `charger()` returns the messages (and the
// API marks the other side's as read), `envoyer(texte)` posts one. `moi` is who is looking:
// 'client' or 'artisane', so each side sees its own messages on the right.
export default function FilMessages({ moi, charger, envoyer, titre = 'Messages' }) {
  const [version, setVersion] = useState(0)
  const fil = useApi(charger, [version])
  const [texte, setTexte] = useState('')
  const [envoi, setEnvoi] = useState(false)
  const [erreur, setErreur] = useState(null)

  async function poster(e) {
    e.preventDefault()
    setEnvoi(true)
    setErreur(null)
    try {
      await envoyer(texte)
      setTexte('')
      setVersion((v) => v + 1)
    } catch (err) {
      setErreur(messageErreurApi(err))
    }
    setEnvoi(false)
  }

  const nomAutre = moi === 'client' ? "L'atelier" : 'Le client'
  return (
    <section className="fil">
      <h3>{titre}</h3>
      <EtatChargement
        statut={fil.statut}
        reessayer={fil.reessayer}
        vide={fil.data?.length === 0}
        messageVide="Aucun message pour l'instant. Posez votre question ci-dessous."
      >
        <ul className="fil__messages" aria-live="polite">
          {fil.data?.map((m) => (
            <li key={m.id} className={`fil__message${m.auteur === moi ? ' fil__message--moi' : ''}`}>
              <span className="fil__auteur">{m.auteur === moi ? 'Vous' : nomAutre} · {formatDate(m.created_at)}</span>
              <p>{m.texte}</p>
            </li>
          ))}
        </ul>
      </EtatChargement>
      <form className="formulaire" onSubmit={poster}>
        <label>
          Votre message
          <textarea rows={3} maxLength={2000} value={texte} onChange={(e) => setTexte(e.target.value)} required />
        </label>
        {erreur && <p className="message-erreur" role="alert">{erreur}</p>}
        <button type="submit" className="bouton" disabled={envoi || texte.trim() === ''}>
          {envoi ? 'Envoi…' : 'Envoyer'}
        </button>
      </form>
    </section>
  )
}
