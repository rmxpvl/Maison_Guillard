import { Outlet } from 'react-router-dom'
import Header from './components/Header.jsx'
import { getCategories } from './api/categories.js'
import { useApi } from './hooks/useApi.js'

// Categories are loaded once here: the header and the catalogue filters both need them.
export default function Layout() {
  const categories = useApi(getCategories, [])
  return (
    <>
      <Header categories={categories.data ?? []} />
      <main className="contenu">
        <Outlet context={{ categories }} />
      </main>
    </>
  )
}
