import { Outlet } from 'react-router-dom'
import { getCategories } from './api/categories.js'
import { useApi } from './hooks/useApi.js'

// Parent route of every page. Categories are loaded once here for the shop pages' filters.
// Header and footer live outside the routes (main.jsx) so page transitions never move them.
export default function Layout() {
  const categories = useApi(getCategories, [])
  return <Outlet context={{ categories }} />
}
