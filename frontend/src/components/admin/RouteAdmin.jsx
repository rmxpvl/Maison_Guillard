import { Navigate, Outlet, useOutletContext } from 'react-router-dom'
import BarreAdmin from './BarreAdmin.jsx'
import { useAuth } from '../../hooks/useAuth.js'

// Parent of every protected /admin page: no token → login page.
export default function RouteAdmin() {
  const { token } = useAuth()
  // Pass the categories from Layout down to the admin pages (product form).
  const contexte = useOutletContext()
  if (!token) return <Navigate to="/admin/connexion" replace />
  return (
    <>
      <BarreAdmin />
      <Outlet context={contexte} />
    </>
  )
}
