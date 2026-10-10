export default function EtatChargement({ statut, reessayer, vide = false, messageVide = '', children }) {
  if (statut === 'chargement') {
    return <p className="etat">Chargement…</p>
  }
  if (statut === 'erreur') {
    return (
      <div className="etat etat--erreur">
        <p>Impossible de charger les données.</p>
        <button type="button" className="bouton" onClick={reessayer}>Réessayer</button>
      </div>
    )
  }
  if (vide) {
    return <p className="etat">{messageVide}</p>
  }
  return children
}
