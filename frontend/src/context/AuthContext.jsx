import { useCallback, useMemo, useState } from 'react'
import { AuthContexte } from './authContexte.js'
import { ApiError, apiRequete } from '../api/client.js'

const CLE = 'maison-guillard-admin'

// sessionStorage: the token disappears when the browser is closed (safer on a shared computer).
function lireJeton() {
  try {
    return sessionStorage.getItem(CLE)
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(lireJeton)

  const enregistrer = useCallback((jeton) => {
    setToken(jeton)
    try {
      if (jeton) sessionStorage.setItem(CLE, jeton)
      else sessionStorage.removeItem(CLE)
    } catch {
      // Storage unavailable: the session lasts until the page is reloaded.
    }
  }, [])

  const connexion = useCallback(
    async (email, motDePasse) => {
      const { token: jeton } = await apiRequete('/auth/login', {
        method: 'POST',
        body: { email, motDePasse },
      })
      enregistrer(jeton)
    },
    [enregistrer],
  )

  const deconnexion = useCallback(() => enregistrer(null), [enregistrer])

  // Admin API call with the token. A 401 means the token expired or is invalid: log out,
  // which makes RouteAdmin send the user back to the login page.
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
    () => ({ token, connexion, deconnexion, appel }),
    [token, connexion, deconnexion, appel],
  )

  return <AuthContexte.Provider value={valeur}>{children}</AuthContexte.Provider>
}
