import { useState } from 'react'
import { useAuth } from '../../hooks/useAuth.js'
import { messageErreurApi } from '../../utils/erreurs.js'

// Photos of an existing product: add one, choose the main one, delete. `apresChangement`
// reloads the product so the list shows what the API saved.
export default function PhotosProduit({ produit, apresChangement }) {
  const { appel } = useAuth()
  const [fichier, setFichier] = useState(null)
  const [envoi, setEnvoi] = useState(false)
  const [erreur, setErreur] = useState(null)

  async function agir(action) {
    setEnvoi(true)
    setErreur(null)
    try {
      await action()
      apresChangement()
    } catch (err) {
      setErreur(messageErreurApi(err))
    }
    setEnvoi(false)
  }

  function ajouter(e) {
    e.preventDefault()
    const formulaire = new FormData()
    formulaire.append('fichier', fichier)
    formulaire.append('ordre', String(produit.photos.length))
    agir(async () => {
      await appel(`/produits/${produit.id}/photos`, { method: 'POST', formulaire })
      setFichier(null)
      e.target.reset()
    })
  }

  return (
    <section className="photos-admin">
      <h2>Photos</h2>
      {produit.photos.length === 0 && <p className="infos__note">Aucune photo pour le moment.</p>}
      <ul className="photos-admin__liste">
        {produit.photos.map((photo) => (
          <li key={photo.id} className="photos-admin__photo">
            <img src={photo.url} alt="" />
            {photo.principale ? (
              <span className="photos-admin__principale">Photo principale</span>
            ) : (
              <button
                type="button"
                className="lien-bouton"
                disabled={envoi}
                onClick={() => agir(() => appel(`/photos/${photo.id}/principale`, { method: 'PATCH' }))}
              >
                Définir comme principale
              </button>
            )}
            <button
              type="button"
              className="lien-bouton"
              disabled={envoi}
              onClick={() => window.confirm('Supprimer cette photo ?') && agir(() => appel(`/photos/${photo.id}`, { method: 'DELETE' }))}
            >
              Supprimer
            </button>
          </li>
        ))}
      </ul>
      <form className="photos-admin__ajout" onSubmit={ajouter}>
        <label>
          Ajouter une photo
          <input type="file" accept="image/*" onChange={(e) => setFichier(e.target.files[0] ?? null)} required />
        </label>
        <button type="submit" className="bouton" disabled={envoi || !fichier}>
          {envoi ? 'Envoi…' : 'Ajouter'}
        </button>
      </form>
      {erreur && <p className="message-erreur" role="alert">{erreur}</p>}
    </section>
  )
}
