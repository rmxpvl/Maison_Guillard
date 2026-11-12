import { useCallback, useEffect, useMemo, useState } from 'react'
import { ContenusContexte } from './contenusContexte.js'
import { apiGet } from '../api/client.js'
import { IMAGES_PAR_DEFAUT } from '../config/imagesParDefaut.js'
import { valeurTexte } from '../utils/contenus.js'

// Loaded once for the whole site. Until it answers (or if the API is down) the original texts and
// photos are shown: a page is never empty because of this.
export function ContenusProvider({ children }) {
  const [contenus, setContenus] = useState({})
  const [version, setVersion] = useState(0)

  useEffect(() => {
    let annule = false
    apiGet('/contenus').then(
      (donnees) => { if (!annule) setContenus(donnees) },
      () => {},
    )
    return () => { annule = true }
  }, [version])

  const recharger = useCallback(() => setVersion((v) => v + 1), [])
  const valeur = useMemo(
    () => ({
      contenus,
      recharger,
      texte: (cle) => valeurTexte(contenus, cle),
      image: (cle) => contenus[cle]?.image_url ?? IMAGES_PAR_DEFAUT[cle],
    }),
    [contenus, recharger],
  )
  return <ContenusContexte.Provider value={valeur}>{children}</ContenusContexte.Provider>
}
