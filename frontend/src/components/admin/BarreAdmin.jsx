import { Link } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth.js'

export default function BarreAdmin() {
  const { deconnexion } = useAuth()
  return (
    <header className="barre-admin">
      <Link to="/admin" className="barre-admin__titre">Maison Guillard · Administration</Link>
      <div className="barre-admin__actions">
        <Link to="/">Voir le site</Link>
        <button type="button" className="bouton bouton--discret" onClick={deconnexion}>
          Déconnexion
        </button>
      </div>
    </header>
  )
}
