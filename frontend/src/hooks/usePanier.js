import { useContext } from 'react'
import { PanierContexte } from '../context/panierContexte.js'

export function usePanier() {
  const contexte = useContext(PanierContexte)
  if (contexte === null) throw new Error('usePanier doit être utilisé dans <PanierProvider>')
  return contexte
}
