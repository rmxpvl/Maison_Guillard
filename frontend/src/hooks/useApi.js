import { useCallback, useEffect, useState } from 'react'

// Runs `load` whenever `deps` change and exposes { statut, data, erreur, reessayer }.
// `cle` identifies the current request: a result stored for an older key means
// the current one is still loading, and late answers from old requests are dropped.
// `load` is a new function on every render, so the effect depends on `cle` only.
export function useApi(load, deps) {
  const [essai, setEssai] = useState(0)
  const cle = JSON.stringify([...deps, essai])
  const [resultat, setResultat] = useState({ cle: null, data: null, erreur: null })

  useEffect(() => {
    let annule = false
    load().then(
      (data) => { if (!annule) setResultat({ cle, data, erreur: null }) },
      (erreur) => { if (!annule) setResultat({ cle, data: null, erreur }) },
    )
    return () => { annule = true }
  }, [cle])

  const reessayer = useCallback(() => setEssai((n) => n + 1), [])

  if (resultat.cle !== cle) return { statut: 'chargement', data: null, erreur: null, reessayer }
  if (resultat.erreur) return { statut: 'erreur', data: null, erreur: resultat.erreur, reessayer }
  return { statut: 'ok', data: resultat.data, erreur: null, reessayer }
}
