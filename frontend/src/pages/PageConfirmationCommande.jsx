import { useEffect } from 'react'
import { Link, Navigate, useLocation } from 'react-router-dom'
import { usePanier } from '../hooks/usePanier.js'
import { formatPrix } from '../utils/produit.js'

export default function PageConfirmationCommande() {
  const { state } = useLocation()
  const { vider } = usePanier()
  const numero = state?.numero

  // The order is saved: the cart can be emptied now. Doing it in the form instead would
  // re-render the form with an empty cart and redirect to /panier before this page shows.
  useEffect(() => {
    if (numero) vider()
  }, [numero, vider])

  if (!numero) return <Navigate to="/" replace />

  return (
    <section className="etat contenu">
      <p className="surtitre">Merci</p>
      <h1>Commande n°{numero} reçue</h1>
      <p>Montant : {formatPrix(state.total)}</p>
      <p>Maison Guillard vous contacte sous 48 h pour le paiement et la livraison.</p>
      <Link to="/boutique">Retour à la boutique</Link>
    </section>
  )
}
