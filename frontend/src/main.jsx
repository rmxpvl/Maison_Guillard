import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import './index.css'
import Layout from './Layout.jsx'
import PageAccueil from './pages/PageAccueil.jsx'
import PageCatalogue from './pages/PageCatalogue.jsx'
import PageContact from './pages/PageContact.jsx'
import PageFicheProduit from './pages/PageFicheProduit.jsx'
import PageIntrouvable from './pages/PageIntrouvable.jsx'
import PageQuiSommesNous from './pages/PageQuiSommesNous.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<PageAccueil />} />
          <Route path="boutique" element={<PageCatalogue />} />
          <Route path="boutique/:slug" element={<PageCatalogue />} />
          <Route path="produits/:id" element={<PageFicheProduit />} />
          <Route path="qui-sommes-nous" element={<PageQuiSommesNous />} />
          <Route path="contact" element={<PageContact />} />
          <Route path="*" element={<PageIntrouvable />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
