import { useEffect } from 'react'
import { Link, Navigate, useLocation } from 'react-router-dom'
import { usePanier } from '../hooks/usePanier.js'

export default function PageConfirmationDemande() {
  const { state } = useLocation()
  const { vider } = usePanier()
  const numero = state?.numero

  // The request is saved: the local one can be emptied now. Doing it in the form instead would
  // re-render the form with an empty request and redirect away before this page shows.
  useEffect(() => {
    if (numero) vider()
  }, [numero, vider])

  if (!numero) return <Navigate to="/" replace />

  return (
    <section className="etat contenu">
      <p className="surtitre">Merci</p>
      <h1>Demande n°{numero} reçue</h1>
      <p>Maison Guillard vous envoie votre devis sous 48 h. Vous recevrez un e-mail avec un lien pour le consulter.</p>
      <Link to="/boutique">Retour à la boutique</Link>
    </section>
  )
}
