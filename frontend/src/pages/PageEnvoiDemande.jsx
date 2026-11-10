import { useEffect, useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { creerDemande } from '../api/demandes.js'
import { useClientAuth } from '../hooks/useClientAuth.js'
import { usePanier } from '../hooks/usePanier.js'
import { messageErreurApi } from '../utils/erreurs.js'
import { lignesPourApi } from '../utils/panier.js'
import { formatPrix } from '../utils/produit.js'

const CHAMPS_VIDES = { nom_client: '', email: '', telephone: '', adresse: '', message_client: '' }

export default function PageEnvoiDemande() {
  const { lignes, total } = usePanier()
  const { token, appel } = useClientAuth()
  const navigate = useNavigate()
  const [champs, setChamps] = useState(CHAMPS_VIDES)
  const [envoi, setEnvoi] = useState(false)
  const [erreur, setErreur] = useState(null)

  // A logged-in customer: the e-mail is already known (and the request will join the account).
  useEffect(() => {
    if (!token) return
    appel('/clients/moi')
      .then((moi) => setChamps((c) => (c.email ? c : { ...c, email: moi.email })))
      .catch(() => {})
  }, [token, appel])

  if (lignes.length === 0) return <Navigate to="/demande" replace />

  function changer(e) {
    setChamps({ ...champs, [e.target.name]: e.target.value })
  }

  async function envoyer(e) {
    e.preventDefault()
    setEnvoi(true)
    setErreur(null)
    try {
      const demande = await creerDemande({
        ...champs,
        telephone: champs.telephone.trim() || null,
        message_client: champs.message_client.trim() || null,
        lignes: lignesPourApi(lignes),
      })
      // The request is emptied by the confirmation page, once it is on screen.
      navigate('/demande/confirmation', { replace: true, state: { numero: demande.id } })
    } catch (err) {
      setErreur(messageErreurApi(err))
      setEnvoi(false)
    }
  }

  return (
    <section className="contenu section deux-colonnes commande">
      <form className="formulaire" onSubmit={envoyer}>
        <h1>Vos coordonnées</h1>
        <label>
          Nom et prénom
          <input name="nom_client" value={champs.nom_client} onChange={changer} required maxLength={100} autoComplete="name" />
        </label>
        <label>
          E-mail
          <input name="email" type="email" value={champs.email} onChange={changer} required autoComplete="email" />
        </label>
        <label>
          Téléphone (facultatif)
          <input name="telephone" type="tel" value={champs.telephone} onChange={changer} maxLength={30} autoComplete="tel" />
        </label>
        <label>
          Adresse de livraison
          <textarea name="adresse" value={champs.adresse} onChange={changer} required maxLength={300} rows={3} autoComplete="street-address" />
        </label>
        <label>
          Message (facultatif)
          <textarea name="message_client" value={champs.message_client} onChange={changer} maxLength={1000} rows={3} />
        </label>
        {erreur && <p className="message-erreur" role="alert">{erreur}</p>}
        <button type="submit" className="bouton bouton--principal" disabled={envoi}>
          {envoi ? 'Envoi…' : 'Envoyer ma demande'}
        </button>
        <p className="infos__note">Rien n'est payé maintenant : vous recevez votre devis sous 48 h.</p>
      </form>
      <aside className="recapitulatif">
        <h2>Récapitulatif</h2>
        <ul>
          {lignes.map((l) => (
            <li key={l.produit_id}>
              <span>
                {l.nom} × {l.quantite}
                {l.teintes.find((t) => t.id === l.teinte_id) && ` · ${l.teintes.find((t) => t.id === l.teinte_id).nom}`}
              </span>
              <span>dès {formatPrix(Number(l.prix) * l.quantite)}</span>
            </li>
          ))}
        </ul>
        <p className="panier__total">Total indicatif : <strong>dès {formatPrix(total)}</strong></p>
        <Link to="/demande">Modifier ma demande</Link>
      </aside>
    </section>
  )
}
