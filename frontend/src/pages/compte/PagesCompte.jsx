import { useState } from 'react'
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom'
import {
  activerCompte,
  inscription,
  motDePasseOublie,
  reinitialiserMotDePasse,
} from '../../api/comptes.js'
import { useClientAuth } from '../../hooks/useClientAuth.js'
import { erreurMotDePasse } from '../../utils/compte.js'
import { messageErreurApi } from '../../utils/erreurs.js'

// Small shared shell: a title, a form, an error line.
function Formulaire({ titre, sousTitre, enfants, erreur, bouton, envoi, onSubmit, pied }) {
  return (
    <section className="contenu section connexion-admin">
      <form className="formulaire" onSubmit={onSubmit}>
        <p className="surtitre">Mon compte</p>
        <h1>{titre}</h1>
        {sousTitre && <p className="infos__note">{sousTitre}</p>}
        {enfants}
        {erreur && <p className="message-erreur" role="alert">{erreur}</p>}
        <button type="submit" className="bouton bouton--principal" disabled={envoi}>{bouton}</button>
        {pied}
      </form>
    </section>
  )
}

function ChampMotDePasse({ etiquette, valeur, onChange, autoComplete }) {
  return (
    <label>
      {etiquette}
      <input type="password" value={valeur} onChange={(e) => onChange(e.target.value)} required autoComplete={autoComplete} />
    </label>
  )
}

export function PageInscription() {
  const [email, setEmail] = useState('')
  const [envoi, setEnvoi] = useState(false)
  const [erreur, setErreur] = useState(null)
  const [fait, setFait] = useState(false)

  async function envoyer(e) {
    e.preventDefault()
    setEnvoi(true)
    setErreur(null)
    try {
      await inscription(email)
      setFait(true)
    } catch (err) {
      setErreur(messageErreurApi(err))
    }
    setEnvoi(false)
  }

  if (fait) {
    return (
      <section className="etat contenu">
        <h1>Vérifiez votre boîte mail</h1>
        <p>
          Si l'adresse {email} est valide, vous allez recevoir un lien pour activer votre compte et
          choisir votre mot de passe (valable 48 h).
        </p>
      </section>
    )
  }
  return (
    <Formulaire
      titre="Créer un compte"
      sousTitre="Suivez vos demandes, vos devis et vos échanges avec l'atelier au même endroit. Nous vous envoyons d'abord un lien pour vérifier votre adresse."
      enfants={
        <label>
          E-mail
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />
        </label>
      }
      erreur={erreur}
      envoi={envoi}
      bouton={envoi ? 'Envoi…' : 'Recevoir mon lien'}
      onSubmit={envoyer}
      pied={<p className="infos__note">Déjà un compte ? <Link to="/compte/connexion">Se connecter</Link></p>}
    />
  )
}

export function PageActivation() {
  const [params] = useSearchParams()
  const token = params.get('token')
  const { enregistrer } = useClientAuth()
  const navigate = useNavigate()
  const [motDePasse, setMotDePasse] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [envoi, setEnvoi] = useState(false)
  const [erreur, setErreur] = useState(null)

  if (!token) return <Navigate to="/compte/inscription" replace />

  async function envoyer(e) {
    e.preventDefault()
    const probleme = erreurMotDePasse(motDePasse, confirmation)
    if (probleme) return setErreur(probleme)
    setEnvoi(true)
    setErreur(null)
    try {
      const { token: jeton } = await activerCompte(token, motDePasse)
      enregistrer(jeton)
      navigate('/compte', { replace: true })
    } catch (err) {
      setErreur(messageErreurApi(err))
      setEnvoi(false)
    }
  }

  return (
    <Formulaire
      titre="Choisissez votre mot de passe"
      sousTitre="Votre adresse e-mail est vérifiée. Vos demandes passées avec cette adresse seront rattachées à votre compte."
      enfants={
        <>
          <ChampMotDePasse etiquette="Mot de passe (8 caractères au moins)" valeur={motDePasse} onChange={setMotDePasse} autoComplete="new-password" />
          <ChampMotDePasse etiquette="Confirmer le mot de passe" valeur={confirmation} onChange={setConfirmation} autoComplete="new-password" />
        </>
      }
      erreur={erreur}
      envoi={envoi}
      bouton={envoi ? 'Activation…' : 'Activer mon compte'}
      onSubmit={envoyer}
    />
  )
}

export function PageConnexionClient() {
  const { token, connexion } = useClientAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [motDePasse, setMotDePasse] = useState('')
  const [envoi, setEnvoi] = useState(false)
  const [erreur, setErreur] = useState(null)

  if (token) return <Navigate to="/compte" replace />

  async function envoyer(e) {
    e.preventDefault()
    setEnvoi(true)
    setErreur(null)
    try {
      await connexion(email, motDePasse)
      navigate('/compte', { replace: true })
    } catch (err) {
      setErreur(err.status === 401 ? 'E-mail ou mot de passe incorrect.' : messageErreurApi(err))
      setEnvoi(false)
    }
  }

  return (
    <Formulaire
      titre="Connexion"
      enfants={
        <>
          <label>
            E-mail
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="username" />
          </label>
          <ChampMotDePasse etiquette="Mot de passe" valeur={motDePasse} onChange={setMotDePasse} autoComplete="current-password" />
        </>
      }
      erreur={erreur}
      envoi={envoi}
      bouton={envoi ? 'Connexion…' : 'Se connecter'}
      onSubmit={envoyer}
      pied={
        <p className="infos__note">
          <Link to="/compte/mot-de-passe-oublie">Mot de passe oublié ?</Link> · <Link to="/compte/inscription">Créer un compte</Link>
        </p>
      }
    />
  )
}

export function PageMotDePasseOublie() {
  const [email, setEmail] = useState('')
  const [envoi, setEnvoi] = useState(false)
  const [erreur, setErreur] = useState(null)
  const [fait, setFait] = useState(false)

  async function envoyer(e) {
    e.preventDefault()
    setEnvoi(true)
    setErreur(null)
    try {
      await motDePasseOublie(email)
      setFait(true)
    } catch (err) {
      setErreur(messageErreurApi(err))
    }
    setEnvoi(false)
  }

  if (fait) {
    return (
      <section className="etat contenu">
        <h1>Vérifiez votre boîte mail</h1>
        <p>Si un compte existe avec cette adresse, vous allez recevoir un lien pour choisir un nouveau mot de passe (valable 1 h).</p>
      </section>
    )
  }
  return (
    <Formulaire
      titre="Mot de passe oublié"
      enfants={
        <label>
          E-mail
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />
        </label>
      }
      erreur={erreur}
      envoi={envoi}
      bouton={envoi ? 'Envoi…' : 'Recevoir un lien'}
      onSubmit={envoyer}
    />
  )
}

export function PageReinitialisation() {
  const [params] = useSearchParams()
  const token = params.get('token')
  const navigate = useNavigate()
  const [motDePasse, setMotDePasse] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [envoi, setEnvoi] = useState(false)
  const [erreur, setErreur] = useState(null)

  if (!token) return <Navigate to="/compte/mot-de-passe-oublie" replace />

  async function envoyer(e) {
    e.preventDefault()
    const probleme = erreurMotDePasse(motDePasse, confirmation)
    if (probleme) return setErreur(probleme)
    setEnvoi(true)
    setErreur(null)
    try {
      await reinitialiserMotDePasse(token, motDePasse)
      navigate('/compte/connexion', { replace: true })
    } catch (err) {
      setErreur(messageErreurApi(err))
      setEnvoi(false)
    }
  }

  return (
    <Formulaire
      titre="Nouveau mot de passe"
      enfants={
        <>
          <ChampMotDePasse etiquette="Nouveau mot de passe (8 caractères au moins)" valeur={motDePasse} onChange={setMotDePasse} autoComplete="new-password" />
          <ChampMotDePasse etiquette="Confirmer le mot de passe" valeur={confirmation} onChange={setConfirmation} autoComplete="new-password" />
        </>
      }
      erreur={erreur}
      envoi={envoi}
      bouton={envoi ? 'Enregistrement…' : 'Enregistrer'}
      onSubmit={envoyer}
    />
  )
}
