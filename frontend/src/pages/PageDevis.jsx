import { useState } from 'react'
import { useParams } from 'react-router-dom'
import EtatChargement from '../components/EtatChargement.jsx'
import PageIntrouvable from './PageIntrouvable.jsx'
import { getSuiviDemande, refuserDevis } from '../api/demandes.js'
import { useApi } from '../hooks/useApi.js'
import { formatDate } from '../utils/admin.js'
import { messageErreurApi } from '../utils/erreurs.js'
import { formatPrix } from '../utils/produit.js'

const GARANTIE = 'Fabrication et livraison garanties sous 15 jours après le paiement.'

function Contact({ d }) {
  if (!d.atelier_email && !d.atelier_telephone) return <>Contactez l'atelier.</>
  return (
    <>
      Contactez l'atelier : {d.atelier_email && <a href={`mailto:${d.atelier_email}`}>{d.atelier_email}</a>}
      {d.atelier_email && d.atelier_telephone && ' · '}
      {d.atelier_telephone}
    </>
  )
}

const FABRICATION = { en_fabrication: 'en fabrication', expediee: 'expédiée', livree: 'livrée' }

// What the customer reads for each state of the request (spec 4.5).
function Etat({ d }) {
  switch (d.statut) {
    case 'nouvelle':
      return <p role="status">Votre devis arrive sous 48 h.</p>
    case 'expiree':
      return (
        <p role="status">
          Ce devis a expiré le {formatDate(d.expire_at)}. <Contact d={d} /> pour en recevoir un nouveau.
        </p>
      )
    case 'refusee':
      return <p role="status">Vous avez refusé ce devis.</p>
    case 'annulee':
      return (
        <p role="status">
          Commande annulée{d.rembourse_at && `, remboursée le ${formatDate(d.rembourse_at)}`}.
        </p>
      )
    case 'payee':
      return (
        <p role="status">
          Paiement reçu le {formatDate(d.payee_at)}. Livraison prévue au plus tard le {formatDate(d.date_limite)}.
        </p>
      )
    case 'en_fabrication':
    case 'expediee':
    case 'livree':
      return (
        <p role="status">
          Statut : {FABRICATION[d.statut]}
          {d.date_limite && `, livraison prévue au plus tard le ${formatDate(d.date_limite)}`}. <Contact d={d} />
        </p>
      )
    default:
      return null
  }
}

// Secret link of a request (/devis/<jeton>): always shows its up-to-date state.
export default function PageDevis() {
  const { jeton } = useParams()
  const [version, setVersion] = useState(0)
  const demande = useApi(() => getSuiviDemande(jeton), [jeton, version])
  const [erreur, setErreur] = useState(null)

  if (demande.erreur?.status === 404) return <PageIntrouvable />

  async function refuser() {
    if (!window.confirm('Refuser ce devis ?')) return
    setErreur(null)
    try {
      await refuserDevis(jeton)
    } catch (err) {
      setErreur(messageErreurApi(err))
    }
    setVersion((v) => v + 1)
  }

  const d = demande.data
  const devisValide = d?.statut === 'devis_envoye'
  const aUnDevis = d?.numero_devis != null
  return (
    <section className="contenu section">
      <EtatChargement statut={demande.statut} reessayer={demande.reessayer}>
        {d && (
          <>
            <p className="surtitre">Demande n°{d.id}{aUnDevis && ` · Devis ${d.numero_devis}`}</p>
            <h1>{aUnDevis ? 'Votre devis' : 'Votre demande'}</h1>
            <p>Demande envoyée le {formatDate(d.created_at)}.</p>
            <Etat d={d} />
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
                    <span>
                      {l.prix_final != null
                        ? formatPrix(Number(l.prix_final) * l.quantite)
                        : `dès ${formatPrix(Number(l.prix_indicatif) * l.quantite)}`}
                    </span>
                  </li>
                ))}
                {aUnDevis && (
                  <>
                    <li><span>Livraison</span><span>{formatPrix(d.frais_livraison ?? 0)}</span></li>
                    <li><strong>Total</strong><strong>{formatPrix(d.total_final)}</strong></li>
                  </>
                )}
              </ul>
            )}
            {d.message_artisane && <p className="devis__message">{d.message_artisane}</p>}
            {devisValide && (
              <>
                <p className="infos__note">
                  Devis valable jusqu'au {formatDate(d.expire_at)}. {GARANTIE}
                </p>
                <div className="detail__statut">
                  <button type="button" className="bouton" onClick={refuser}>Refuser le devis</button>
                </div>
                <p className="infos__note">
                  Le paiement en ligne sera bientôt disponible ; en attendant, <Contact d={d} />
                </p>
              </>
            )}
            {aUnDevis && (
              <p>
                <a href={`/api/demandes/suivi/${encodeURIComponent(jeton)}/devis.pdf`} target="_blank" rel="noreferrer">
                  Télécharger le devis en PDF
                </a>
              </p>
            )}
            {erreur && <p className="message-erreur" role="alert">{erreur}</p>}
          </>
        )}
      </EtatChargement>
    </section>
  )
}
