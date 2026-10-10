import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import './index.css'
import Layout from './Layout.jsx'
import PageCatalogue from './pages/PageCatalogue.jsx'
import PageIntrouvable from './pages/PageIntrouvable.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<PageCatalogue />} />
          <Route path="categorie/:slug" element={<PageCatalogue />} />
          <Route path="*" element={<PageIntrouvable />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
