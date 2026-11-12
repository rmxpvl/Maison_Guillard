import { useSearchParams } from 'react-router-dom'
import OngletActualites from '../../components/admin/OngletActualites.jsx'
import OngletCategories from '../../components/admin/OngletCategories.jsx'
import OngletDemandes from '../../components/admin/OngletDemandes.jsx'
import OngletPagesSite from '../../components/admin/OngletPagesSite.jsx'
import OngletProduits from '../../components/admin/OngletProduits.jsx'
import OngletReglages from '../../components/admin/OngletReglages.jsx'
import OngletTeintes from '../../components/admin/OngletTeintes.jsx'
import TableauDeBord from '../../components/admin/TableauDeBord.jsx'

const PAGES = {
  accueil: TableauDeBord,
  demandes: OngletDemandes,
  actualites: OngletActualites,
  pages: OngletPagesSite,
  produits: OngletProduits,
  categories: OngletCategories,
  teintes: OngletTeintes,
  reglages: OngletReglages,
}

// The part shown is in the URL (?onglet=…): reload, back button and links from the home page all work.
// The menu on the left (MenuAdmin) is how the artisane moves around.
export default function PageAdmin() {
  const [params] = useSearchParams()
  const demande = params.get('onglet')
  const Page = PAGES[demande] ?? TableauDeBord
  return <Page />
}
