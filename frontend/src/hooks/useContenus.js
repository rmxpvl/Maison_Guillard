import { useContext } from 'react'
import { ContenusContexte } from '../context/contenusContexte.js'

// texte(cle) and image(cle): the artisane's version of a block, or the original one.
export function useContenus() {
  const contexte = useContext(ContenusContexte)
  if (contexte === null) throw new Error('useContenus doit être utilisé dans <ContenusProvider>')
  return contexte
}
