import { useContext } from 'react'
import { ClientAuthContexte } from '../context/clientAuthContexte.js'

export function useClientAuth() {
  const contexte = useContext(ClientAuthContexte)
  if (contexte === null) throw new Error('useClientAuth doit être utilisé dans <ClientAuthProvider>')
  return contexte
}
