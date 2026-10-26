import { useContext } from 'react'
import { AuthContexte } from '../context/authContexte.js'

export function useAuth() {
  const contexte = useContext(AuthContexte)
  if (contexte === null) throw new Error('useAuth doit être utilisé dans <AuthProvider>')
  return contexte
}
