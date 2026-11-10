import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Route } from 'react-router-dom'
import './index.css'
import './admin.css'
import Layout from './Layout.jsx'
import Footer from './components/Footer.jsx'
import Header from './components/Header.jsx'
import TransitionPages from './components/TransitionPages.jsx'
import RouteAdmin from './components/admin/RouteAdmin.jsx'
import { AuthProvider } from './context/AuthContext.jsx'
import { ClientAuthProvider } from './context/ClientAuthContext.jsx'
import { PanierProvider } from './context/PanierContext.jsx'
import PageCompte from './pages/compte/PageCompte.jsx'
import {
  PageActivation,
  PageConnexionClient,
  PageInscription,
  PageMotDePasseOublie,
  PageReinitialisation,
} from './pages/compte/PagesCompte.jsx'
import PageAdmin from './pages/admin/PageAdmin.jsx'
import PageConnexionAdmin from './pages/admin/PageConnexionAdmin.jsx'
import PageProduitAdmin from './pages/admin/PageProduitAdmin.jsx'
import PageAccueil from './pages/PageAccueil.jsx'
import PageBoutique from './pages/PageBoutique.jsx'
import PageCgv from './pages/PageCgv.jsx'
import PageConfirmationDemande from './pages/PageConfirmationDemande.jsx'
import PageContact from './pages/PageContact.jsx'
import PageFicheProduit from './pages/PageFicheProduit.jsx'
import PageDemande from './pages/PageDemande.jsx'
import PageDevis from './pages/PageDevis.jsx'
import PageEnvoiDemande from './pages/PageEnvoiDemande.jsx'
import PageIntrouvable from './pages/PageIntrouvable.jsx'
import PageUnivers from './pages/PageUnivers.jsx'
import PageQuiSommesNous from './pages/PageQuiSommesNous.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AuthProvider>
      <ClientAuthProvider>
      <PanierProvider>
        <BrowserRouter>
          <Header />
          <TransitionPages>
            <Route element={<Layout />}>
              <Route index element={<PageAccueil />} />
              <Route path="boutique" element={<PageBoutique />} />
              <Route path="boutique/:univers" element={<PageUnivers />} />
              <Route path="boutique/:univers/:categorie" element={<PageUnivers />} />
              <Route path="produits/:id" element={<PageFicheProduit />} />
              <Route path="qui-sommes-nous" element={<PageQuiSommesNous />} />
              <Route path="contact" element={<PageContact />} />
              <Route path="demande" element={<PageDemande />} />
              <Route path="demande/envoi" element={<PageEnvoiDemande />} />
              <Route path="demande/confirmation" element={<PageConfirmationDemande />} />
              <Route path="devis/:jeton" element={<PageDevis />} />
              <Route path="cgv" element={<PageCgv />} />
              <Route path="compte" element={<PageCompte />} />
              <Route path="compte/inscription" element={<PageInscription />} />
              <Route path="compte/activation" element={<PageActivation />} />
              <Route path="compte/connexion" element={<PageConnexionClient />} />
              <Route path="compte/mot-de-passe-oublie" element={<PageMotDePasseOublie />} />
              <Route path="compte/reinitialisation" element={<PageReinitialisation />} />
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
      </ClientAuthProvider>
    </AuthProvider>
  </StrictMode>,
)
