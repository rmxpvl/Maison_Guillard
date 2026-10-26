import { useState } from 'react'
import { useApi } from '../../hooks/useApi.js'
import { useAuth } from '../../hooks/useAuth.js'
import { messageErreurApi } from '../../utils/erreurs.js'

export default function InterrupteurEmail() {
  const { appel } = useAuth()
  const [version, setVersion] = useState(0)
  const parametres = useApi(() => appel('/parametres'), [version])
  const [erreur, setErreur] = useState(null)

  async function basculer(e) {
    setErreur(null)
    try {
      await appel('/parametres', { method: 'PUT', body: { email_commande_actif: e.target.checked } })
    } catch (err) {
      setErreur(messageErreurApi(err))
    }
    setVersion((v) => v + 1)
  }

  return (
    <div className="interrupteur">
      <label>
        <input
          type="checkbox"
          checked={parametres.data?.email_commande_actif ?? false}
          disabled={parametres.statut !== 'ok'}
          onChange={basculer}
        />
        Recevoir un e-mail (et envoyer un accusé de réception au client) à chaque commande et
        demande de devis
      </label>
      {erreur && <p className="message-erreur" role="alert">{erreur}</p>}
    </div>
  )
}
