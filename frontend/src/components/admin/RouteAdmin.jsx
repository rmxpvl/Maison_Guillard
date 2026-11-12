import { useCallback, useMemo, useState } from 'react'
import { Navigate, Outlet, useOutletContext } from 'react-router-dom'
import MenuAdmin from './MenuAdmin.jsx'
import { ResumeAdminContexte } from '../../context/resumeAdminContexte.js'
import { useApi } from '../../hooks/useApi.js'
import { useAuth } from '../../hooks/useAuth.js'

// Parent of every protected /admin page: no token → login page. Draws the menu and the page.
export default function RouteAdmin() {
  const { token, appel } = useAuth()
  // Pass the categories from Layout down to the admin pages (product form).
  const contexte = useOutletContext()
  const [version, setVersion] = useState(0)
  const demandes = useApi(() => (token ? appel('/demandes') : Promise.resolve([])), [token, appel, version])
  const recharger = useCallback(() => setVersion((v) => v + 1), [])

  const resume = useMemo(
    () => ({ statut: demandes.statut, demandes: demandes.data ?? [], recharger, reessayer: demandes.reessayer }),
    [demandes.statut, demandes.data, recharger, demandes.reessayer],
  )

  if (!token) return <Navigate to="/admin/connexion" replace />
  return (
    <ResumeAdminContexte.Provider value={resume}>
      <div className="admin-app">
        <MenuAdmin />
        <main className="admin-contenu">
          <Outlet context={contexte} />
        </main>
      </div>
    </ResumeAdminContexte.Provider>
  )
}
