import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import './index.css'
import Layout from './Layout.jsx'
import PageCatalogue from './pages/PageCatalogue.jsx'
import PageFicheProduit from './pages/PageFicheProduit.jsx'
import PageIntrouvable from './pages/PageIntrouvable.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="boutique" element={<PageCatalogue />} />
          <Route path="boutique/:slug" element={<PageCatalogue />} />
          <Route path="produits/:id" element={<PageFicheProduit />} />
          <Route path="*" element={<PageIntrouvable />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
