import { useParams } from 'react-router-dom'
import EtatChargement from '../components/EtatChargement.jsx'
import PageIntrouvable from './PageIntrouvable.jsx'
import { getSuiviDemande } from '../api/demandes.js'
import { useApi } from '../hooks/useApi.js'
import { formatDate } from '../utils/admin.js'
import { formatPrix } from '../utils/produit.js'

const MESSAGES = {
  nouvelle: 'Votre devis arrive sous 48 h.',
  refusee: 'Vous avez refusé ce devis.',
  annulee: 'Cette demande a été annulée.',
}

// Secret link of a request (/devis/<jeton>): always shows its up-to-date state.
export default function PageDevis() {
  const { jeton } = useParams()
  const demande = useApi(() => getSuiviDemande(jeton), [jeton])

  if (demande.erreur?.status === 404) return <PageIntrouvable />

  const d = demande.data
  return (
    <section className="contenu section">
      <EtatChargement statut={demande.statut} reessayer={demande.reessayer}>
        {d && (
          <>
            <p className="surtitre">Demande n°{d.id}</p>
            <h1>Votre demande</h1>
            <p>Envoyée le {formatDate(d.created_at)}.</p>
            {MESSAGES[d.statut] && <p role="status">{MESSAGES[d.statut]}</p>}
            {d.description_projet && <p>{d.description_projet}</p>}
            {d.lignes.length > 0 && (
              <ul className="detail__lignes">
                {d.lignes.map((l) => (
                  <li key={l.id}>
                    <span>
                      {l.libelle} × {l.quantite}
                      {l.teinte_nom && ` · ${l.teinte_nom}`}
                      {l.souhait && ` · « ${l.souhait} »`}
                    </span>
                    <span>dès {formatPrix(Number(l.prix_indicatif) * l.quantite)}</span>
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </EtatChargement>
    </section>
  )
}
