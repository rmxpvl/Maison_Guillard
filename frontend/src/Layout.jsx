import { Outlet } from 'react-router-dom'
import Footer from './components/Footer.jsx'
import Header from './components/Header.jsx'
import { getCategories } from './api/categories.js'
import { useApi } from './hooks/useApi.js'

// Categories are loaded once here for the shop pages' filters.
export default function Layout() {
  const categories = useApi(getCategories, [])
  return (
    <>
      <Header />
      <main>
        <Outlet context={{ categories }} />
      </main>
      <Footer />
    </>
  )
}
