import { useCallback, useEffect, useMemo, useState } from 'react'
import { PanierContexte } from './panierContexte.js'
import * as panier from '../utils/panier.js'

const CLE = 'maison-guillard-panier'

// Private browsing or blocked storage can make localStorage throw: start empty then.
function lirePanier() {
  try {
    return panier.lignesValides(JSON.parse(localStorage.getItem(CLE)))
  } catch {
    return []
  }
}

export function PanierProvider({ children }) {
  const [lignes, setLignes] = useState(lirePanier)

  useEffect(() => {
    try {
      localStorage.setItem(CLE, JSON.stringify(lignes))
    } catch {
      // Storage unavailable: the cart still works until the page is closed.
    }
  }, [lignes])

  // useCallback with no deps: same function on every render, safe to use in effects.
  const ajouter = useCallback((produit) => setLignes((l) => panier.ajouterLigne(l, produit)), [])
  const changerQuantite = useCallback(
    (produitId, quantite) => setLignes((l) => panier.changerQuantiteLigne(l, produitId, quantite)),
    [],
  )
  const retirer = useCallback((produitId) => setLignes((l) => panier.retirerLigne(l, produitId)), [])
  const vider = useCallback(() => setLignes([]), [])

  const valeur = useMemo(
    () => ({
      lignes,
      ajouter,
      changerQuantite,
      retirer,
      vider,
      nombreArticles: panier.compterArticles(lignes),
      total: panier.totalPanier(lignes),
    }),
    [lignes, ajouter, changerQuantite, retirer, vider],
  )

  return <PanierContexte.Provider value={valeur}>{children}</PanierContexte.Provider>
}
