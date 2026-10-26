import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { creerCommande } from '../api/commandes.js'
import { usePanier } from '../hooks/usePanier.js'
import { messageErreurApi } from '../utils/erreurs.js'
import { lignesPourApi } from '../utils/panier.js'
import { formatPrix } from '../utils/produit.js'

const CHAMPS_VIDES = { nom_client: '', email: '', telephone: '', adresse: '' }

export default function PageFormulaireCommande() {
  const { lignes, total } = usePanier()
  const navigate = useNavigate()
  const [champs, setChamps] = useState(CHAMPS_VIDES)
  const [envoi, setEnvoi] = useState(false)
  const [erreur, setErreur] = useState(null)

  if (lignes.length === 0) return <Navigate to="/panier" replace />

  function changer(e) {
    setChamps({ ...champs, [e.target.name]: e.target.value })
  }

  async function envoyer(e) {
    e.preventDefault()
    setEnvoi(true)
    setErreur(null)
    try {
      const commande = await creerCommande({
        ...champs,
        telephone: champs.telephone.trim() || null,
        lignes: lignesPourApi(lignes),
      })
      // The cart is emptied by the confirmation page, once it is on screen.
      navigate('/commande/confirmation', {
        replace: true,
        state: { numero: commande.id, total: commande.total },
      })
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
        {erreur && <p className="message-erreur" role="alert">{erreur}</p>}
        <button type="submit" className="bouton bouton--principal" disabled={envoi}>
          {envoi ? 'Envoi…' : 'Confirmer la commande'}
        </button>
        <p className="infos__note">Aucun paiement en ligne : Maison Guillard vous contacte pour le paiement et la livraison.</p>
      </form>
      <aside className="recapitulatif">
        <h2>Récapitulatif</h2>
        <ul>
          {lignes.map((l) => (
            <li key={l.produit_id}>
              <span>{l.nom} × {l.quantite}</span>
              <span>{formatPrix(Number(l.prix) * l.quantite)}</span>
            </li>
          ))}
        </ul>
        <p className="panier__total">Total : <strong>{formatPrix(total)}</strong></p>
        <Link to="/panier">Modifier le panier</Link>
      </aside>
    </section>
  )
}
