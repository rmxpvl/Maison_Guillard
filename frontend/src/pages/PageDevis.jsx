import { useEffect, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import EtatChargement from '../components/EtatChargement.jsx'
import FilMessages from '../components/FilMessages.jsx'
import PageIntrouvable from './PageIntrouvable.jsx'
import { annulerCommande, envoyerMessageDemande, getMessagesDemande, getSuiviDemande, payerDevis, refuserDevis } from '../api/demandes.js'
import { useApi } from '../hooks/useApi.js'
import { useClientAuth } from '../hooks/useClientAuth.js'
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
  const [params] = useSearchParams()
  const { token: compteConnecte } = useClientAuth()
  const retourPaiement = params.get('paiement')
  const [version, setVersion] = useState(0)
  const demande = useApi(() => getSuiviDemande(jeton), [jeton, version])
  const [erreur, setErreur] = useState(null)
  const [cgv, setCgv] = useState(false)
  const [envoi, setEnvoi] = useState(false)
  const [essais, setEssais] = useState(0)

  const statut = demande.data?.statut
  // Back from Stripe: the payment is confirmed by Stripe's signed webhook, which can take a few
  // seconds. Refresh every 2.5 s, for one minute at most, until the request shows as paid.
  const attente = retourPaiement === 'ok' && statut !== undefined && statut !== 'payee' && essais < 24
  useEffect(() => {
    if (!attente) return undefined
    const minuteur = setTimeout(() => {
      setEssais((n) => n + 1)
      setVersion((v) => v + 1)
    }, 2500)
    return () => clearTimeout(minuteur)
  }, [attente, essais])

  if (demande.erreur?.status === 404) return <PageIntrouvable />

  async function payer() {
    setErreur(null)
    setEnvoi(true)
    try {
      const { url } = await payerDevis(jeton)
      window.location.href = url // Stripe's hosted payment page
    } catch (err) {
      setErreur(messageErreurApi(err))
      setEnvoi(false)
    }
  }

  async function annuler() {
    if (!window.confirm('Annuler votre commande ? Vous serez remboursé en totalité.')) return
    setErreur(null)
    try {
      await annulerCommande(jeton)
    } catch (err) {
      setErreur(messageErreurApi(err))
    }
    setVersion((v) => v + 1)
  }

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
            {attente && <p role="status">Paiement en cours de confirmation…</p>}
            {retourPaiement === 'ok' && !attente && d.statut !== 'payee' && (
              <p role="status">
                Votre paiement est en cours de confirmation : actualisez cette page dans un instant.
              </p>
            )}
            {retourPaiement === 'annule' && d.statut === 'devis_envoye' && (
              <p role="status">Paiement annulé : vous pouvez réessayer quand vous voulez.</p>
            )}
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
                <label className="case">
                  <input type="checkbox" checked={cgv} onChange={(e) => setCgv(e.target.checked)} />
                  <span>J'accepte les <Link to="/cgv">conditions générales de vente</Link></span>
                </label>
                <div className="detail__statut">
                  <button type="button" className="bouton bouton--principal" onClick={payer} disabled={!cgv || envoi}>
                    {envoi ? 'Redirection…' : 'Accepter et payer'}
                  </button>
                  <button type="button" className="bouton" onClick={refuser}>Refuser le devis</button>
                </div>
                <p className="infos__note">Paiement sécurisé par carte, sur la page de notre prestataire Stripe.</p>
              </>
            )}
            {d.statut === 'payee' && (
              <div className="detail__statut">
                <button type="button" className="bouton" onClick={annuler}>Annuler ma commande</button>
                <span className="infos__note">Remboursement total tant que la fabrication n'a pas commencé.</span>
              </div>
            )}
            {aUnDevis && (
              <p>
                <a href={`/api/demandes/suivi/${encodeURIComponent(jeton)}/devis.pdf`} target="_blank" rel="noreferrer">
                  Télécharger le devis en PDF
                </a>
              </p>
            )}
            {erreur && <p className="message-erreur" role="alert">{erreur}</p>}
            <FilMessages
              moi="client"
              charger={() => getMessagesDemande(jeton)}
              envoyer={(texte) => envoyerMessageDemande(jeton, texte)}
              titre="Vos échanges avec l'atelier"
            />
            <p className="infos__note">
              {compteConnecte
                ? <Link to="/compte">← Mes demandes</Link>
                : <>Retrouvez toutes vos demandes au même endroit : <Link to="/compte/inscription">créer un compte</Link> avec cette adresse e-mail.</>}
            </p>
          </>
        )}
      </EtatChargement>
    </section>
  )
}
