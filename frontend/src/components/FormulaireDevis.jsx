import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { creerDevis } from '../api/devis.js'
import { getProduit } from '../api/produits.js'
import { useApi } from '../hooks/useApi.js'
import { messageErreurApi } from '../utils/erreurs.js'
import { parseIdProduit } from '../utils/produit.js'

const CHAMPS_VIDES = { nom_client: '', email: '', telephone: '', description_projet: '' }

// Quote request. Opened from a product page, the URL carries ?produit=<id>: the form then
// says which piece it is about and sends its id. A wrong or unknown id is simply ignored.
export default function FormulaireDevis() {
  const [params] = useSearchParams()
  const produitId = parseIdProduit(params.get('produit'))
  const produit = useApi(
    () => (produitId === null ? Promise.resolve(null) : getProduit(produitId)),
    [produitId],
  )
  const [champs, setChamps] = useState(CHAMPS_VIDES)
  const [envoi, setEnvoi] = useState(false)
  const [erreur, setErreur] = useState(null)
  const [numero, setNumero] = useState(null)
  const formulaire = useRef(null)

  // Coming from a product page: bring the form into view instead of the top of the page.
  useEffect(() => {
    if (produitId !== null) formulaire.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [produitId])

  const produitConcerne = produit.data

  function changer(e) {
    setChamps({ ...champs, [e.target.name]: e.target.value })
  }

  async function envoyer(e) {
    e.preventDefault()
    setEnvoi(true)
    setErreur(null)
    try {
      const devis = await creerDevis({
        ...champs,
        telephone: champs.telephone.trim() || null,
        produit_id: produitConcerne?.id ?? null,
      })
      setNumero(devis.id)
      setChamps(CHAMPS_VIDES)
    } catch (err) {
      setErreur(messageErreurApi(err))
    }
    setEnvoi(false)
  }

  if (numero) {
    return (
      <div className="formulaire" role="status">
        <h2>Demande n°{numero} envoyée</h2>
        <p>Maison Guillard vous répond sous 48 h.</p>
      </div>
    )
  }

  return (
    <form ref={formulaire} className="formulaire" onSubmit={envoyer}>
      <h2>Demande de devis</h2>
      {produitConcerne && (
        <p className="formulaire__sujet">À propos de : <strong>{produitConcerne.nom}</strong></p>
      )}
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
        Votre projet
        <textarea
          name="description_projet"
          value={champs.description_projet}
          onChange={changer}
          required
          minLength={10}
          maxLength={2000}
          rows={6}
          placeholder="Dimensions, essence de bois, usage, délai souhaité…"
        />
      </label>
      {erreur && <p className="message-erreur" role="alert">{erreur}</p>}
      <button type="submit" className="bouton bouton--principal" disabled={envoi}>
        {envoi ? 'Envoi…' : 'Envoyer la demande'}
      </button>
    </form>
  )
}
