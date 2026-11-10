import { useCallback, useMemo, useState } from 'react'
import { ClientAuthContexte } from './clientAuthContexte.js'
import { ApiError, apiRequete } from '../api/client.js'

const CLE = 'maison-guillard-client'

// localStorage: a customer stays logged in between visits (the admin uses sessionStorage).
function lireJeton() {
  try {
    return localStorage.getItem(CLE)
  } catch {
    return null
  }
}

// Customer session. Separate from the admin one: a customer token never opens the back-office.
export function ClientAuthProvider({ children }) {
  const [token, setToken] = useState(lireJeton)

  const enregistrer = useCallback((jeton) => {
    setToken(jeton)
    try {
      if (jeton) localStorage.setItem(CLE, jeton)
      else localStorage.removeItem(CLE)
    } catch {
      // Storage unavailable: the session lasts until the page is reloaded.
    }
  }, [])

  const connexion = useCallback(
    async (email, motDePasse) => {
      const { token: jeton } = await apiRequete('/clients/connexion', {
        method: 'POST',
        body: { email, mot_de_passe: motDePasse },
      })
      enregistrer(jeton)
    },
    [enregistrer],
  )

  const deconnexion = useCallback(() => enregistrer(null), [enregistrer])

  // Customer API call with the token. A 401 means it expired or is invalid: log out.
  const appel = useCallback(
    async (path, options = {}) => {
      try {
        return await apiRequete(path, { ...options, token })
      } catch (erreur) {
        if (erreur instanceof ApiError && erreur.status === 401) enregistrer(null)
        throw erreur
      }
    },
    [token, enregistrer],
  )

  const valeur = useMemo(
    () => ({ token, enregistrer, connexion, deconnexion, appel }),
    [token, enregistrer, connexion, deconnexion, appel],
  )

  return <ClientAuthContexte.Provider value={valeur}>{children}</ClientAuthContexte.Provider>
}
