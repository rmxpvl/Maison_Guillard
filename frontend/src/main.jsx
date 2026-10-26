import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Route } from 'react-router-dom'
import './index.css'
import Layout from './Layout.jsx'
import Footer from './components/Footer.jsx'
import Header from './components/Header.jsx'
import TransitionPages from './components/TransitionPages.jsx'
import RouteAdmin from './components/admin/RouteAdmin.jsx'
import { AuthProvider } from './context/AuthContext.jsx'
import { PanierProvider } from './context/PanierContext.jsx'
import PageAdmin from './pages/admin/PageAdmin.jsx'
import PageConnexionAdmin from './pages/admin/PageConnexionAdmin.jsx'
import PageProduitAdmin from './pages/admin/PageProduitAdmin.jsx'
import PageAccueil from './pages/PageAccueil.jsx'
import PageCatalogue from './pages/PageCatalogue.jsx'
import PageConfirmationCommande from './pages/PageConfirmationCommande.jsx'
import PageContact from './pages/PageContact.jsx'
import PageFicheProduit from './pages/PageFicheProduit.jsx'
import PageFormulaireCommande from './pages/PageFormulaireCommande.jsx'
import PageIntrouvable from './pages/PageIntrouvable.jsx'
import PagePanier from './pages/PagePanier.jsx'
import PageQuiSommesNous from './pages/PageQuiSommesNous.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AuthProvider>
      <PanierProvider>
        <BrowserRouter>
          <Header />
          <TransitionPages>
            <Route element={<Layout />}>
              <Route index element={<PageAccueil />} />
              <Route path="boutique" element={<PageCatalogue />} />
              <Route path="boutique/:slug" element={<PageCatalogue />} />
              <Route path="produits/:id" element={<PageFicheProduit />} />
              <Route path="qui-sommes-nous" element={<PageQuiSommesNous />} />
              <Route path="contact" element={<PageContact />} />
              <Route path="panier" element={<PagePanier />} />
              <Route path="commande" element={<PageFormulaireCommande />} />
              <Route path="commande/confirmation" element={<PageConfirmationCommande />} />
              <Route path="admin/connexion" element={<PageConnexionAdmin />} />
              <Route path="admin" element={<RouteAdmin />}>
                <Route index element={<PageAdmin />} />
                <Route path="produits/nouveau" element={<PageProduitAdmin />} />
                <Route path="produits/:id" element={<PageProduitAdmin />} />
              </Route>
              <Route path="*" element={<PageIntrouvable />} />
            </Route>
          </TransitionPages>
          <Footer />
        </BrowserRouter>
      </PanierProvider>
    </AuthProvider>
  </StrictMode>,
)
