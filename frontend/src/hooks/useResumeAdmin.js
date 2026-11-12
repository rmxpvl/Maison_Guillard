import { useContext } from 'react'
import { ResumeAdminContexte } from '../context/resumeAdminContexte.js'

export function useResumeAdmin() {
  const contexte = useContext(ResumeAdminContexte)
  if (contexte === null) throw new Error('useResumeAdmin doit être utilisé dans <RouteAdmin>')
  return contexte
}
