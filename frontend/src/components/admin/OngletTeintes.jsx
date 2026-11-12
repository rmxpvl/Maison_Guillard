import { useRef, useState } from 'react'
import EtatChargement from '../EtatChargement.jsx'
import { useApi } from '../../hooks/useApi.js'
import { useAuth } from '../../hooks/useAuth.js'
import { messageErreurApi } from '../../utils/erreurs.js'

export default function OngletTeintes() {
  const { appel } = useAuth()
  const [version, setVersion] = useState(0)
  const teintes = useApi(() => appel('/teintes'), [appel, version])
  const [message, setMessage] = useState(null)
  const [nom, setNom] = useState('')
  const [ordre, setOrdre] = useState('0')
  const fichierCreation = useRef(null)

  async function agir(action, succes) {
    setMessage(null)
    try {
      await action()
      if (succes) setMessage(succes)
      setVersion((v) => v + 1)
      return true
    } catch (err) {
      setMessage(messageErreurApi(err))
      return false
    }
  }

  async function creer(e) {
    e.preventDefault()
    const formulaire = new FormData()
    formulaire.append('nom', nom.trim())
    formulaire.append('ordre', ordre)
    formulaire.append('fichier', fichierCreation.current.files[0])
    const ok = await agir(() => appel('/teintes', { method: 'POST', formulaire }), `Teinte « ${nom.trim()} » créée.`)
    if (ok) {
      setNom('')
      setOrdre('0')
      e.target.reset()
    }
  }

  const modifier = (t, corps) => agir(() => appel(`/teintes/${t.id}`, { method: 'PUT', body: corps }))

  function changerImage(t, fichier) {
    if (!fichier) return
    const formulaire = new FormData()
    formulaire.append('fichier', fichier)
    agir(() => appel(`/teintes/${t.id}/image`, { method: 'POST', formulaire }), `Image de « ${t.nom} » remplacée.`)
  }

  async function supprimer(t) {
    if (!window.confirm(`Supprimer la teinte « ${t.nom} » ?`)) return
    await agir(() => appel(`/teintes/${t.id}`, { method: 'DELETE' }), `« ${t.nom} » supprimée.`)
  }

  return (
    <div className="page-admin">
      <header className="page-admin__entete">
        <div>
          <h1>Finitions</h1>
          <p className="page-admin__intro">Les finitions (essence de bois, teinte, vernis…) que vos clients peuvent choisir sur une pièce. Ajoutez une petite image pour que le client voie le rendu, puis cochez la finition sur chaque produit concerné.</p>
        </div>
      </header>
      {message && <p className="onglet__message" role="status">{message}</p>}

      <form className="formulaire formulaire--ligne" onSubmit={creer}>
        <label>
          Nom
          <input value={nom} onChange={(e) => setNom(e.target.value)} required maxLength={40} />
        </label>
        <label>
          Ordre
          <input type="number" min="0" value={ordre} onChange={(e) => setOrdre(e.target.value)} />
        </label>
        <label>
          Image
          <input type="file" accept="image/*" ref={fichierCreation} required />
        </label>
        <button type="submit" className="bouton bouton--principal">Ajouter</button>
      </form>

      <EtatChargement statut={teintes.statut} reessayer={teintes.reessayer}
        vide={teintes.data?.length === 0} messageVide="Aucune teinte pour l'instant.">
        <table className="tableau">
          <thead>
            <tr>
              <th>Image</th><th>Nom</th><th>Ordre</th><th>Active</th>
              <th><span className="visuellement-cache">Actions</span></th>
            </tr>
          </thead>
          <tbody>
            {teintes.data?.map((t) => (
              <tr key={t.id}>
                <td><img src={t.image_url} alt="" className="tableau__vignette" /></td>
                <td>{t.nom}</td>
                <td>{t.ordre}</td>
                <td>
                  <input type="checkbox" aria-label={`Teinte ${t.nom} active`} checked={t.active}
                    onChange={(e) => modifier(t, { active: e.target.checked })} />
                </td>
                <td className="tableau__actions">
                  <label className="lien-bouton">
                    Changer l'image
                    <input type="file" accept="image/*" hidden onChange={(e) => changerImage(t, e.target.files[0])} />
                  </label>
                  <button type="button" className="lien-bouton" onClick={() => supprimer(t)}>Supprimer</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </EtatChargement>
    </div>
  )
}
