import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { ApiError } from '../../api/client.js'
import Logo from '../../components/Logo.jsx'
import { useAuth } from '../../hooks/useAuth.js'
import { messageErreurApi } from '../../utils/erreurs.js'

export default function PageConnexionAdmin() {
  const { token, connexion } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [motDePasse, setMotDePasse] = useState('')
  const [visible, setVisible] = useState(false)
  const [envoi, setEnvoi] = useState(false)
  const [erreur, setErreur] = useState(null)

  if (token) return <Navigate to="/admin" replace />

  async function envoyer(e) {
    e.preventDefault()
    setEnvoi(true)
    setErreur(null)
    try {
      await connexion(email, motDePasse)
      navigate('/admin', { replace: true })
    } catch (err) {
      setErreur(
        err instanceof ApiError && err.status === 401
          ? 'E-mail ou mot de passe incorrect.'
          : messageErreurApi(err),
      )
      setEnvoi(false)
    }
  }

  return (
    <section className="admin-app admin-app--connexion">
      <form className="formulaire admin-connexion" onSubmit={envoyer}>
        <Logo />
        <h1>Gestion du site</h1>
        <p className="page-admin__intro">Connectez-vous pour gérer vos produits, vos devis et vos commandes.</p>
        <label>
          E-mail
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="username" />
        </label>
        <label>
          Mot de passe
          <span className="champ-mdp">
            <input type={visible ? 'text' : 'password'} value={motDePasse} onChange={(e) => setMotDePasse(e.target.value)} required autoComplete="current-password" />
            <button type="button" className="champ-mdp__bouton" aria-pressed={visible} onClick={() => setVisible((v) => !v)}>
              {visible ? 'Masquer' : 'Afficher'}
            </button>
          </span>
        </label>
        {erreur && <p className="message-erreur" role="alert">{erreur}</p>}
        <button type="submit" className="bouton bouton--principal" disabled={envoi}>
          {envoi ? 'Connexion…' : 'Se connecter'}
        </button>
      </form>
    </section>
  )
}
