import { useState } from 'react'
import { photoPrincipale } from '../utils/produit.js'

export default function GaleriePhotos({ photos, nom }) {
  const [selectionId, setSelectionId] = useState(null)

  if (photos.length === 0) {
    return <div className="galerie"><div className="photo-vide">Photo à venir</div></div>
  }

  const affichee = photos.find((p) => p.id === selectionId) ?? photoPrincipale(photos)

  return (
    <div className="galerie">
      {/* All photos are stacked; only the selected one is opaque, so CSS cross-fades them. */}
      <div className="galerie__cadre">
        {photos.map((p) => {
          const visible = p.id === affichee.id
          return (
            <img
              key={p.id}
              src={p.url}
              alt={visible ? nom : ''}
              aria-hidden={!visible}
              className={`galerie__grande${visible ? ' galerie__grande--visible' : ''}`}
            />
          )
        })}
      </div>
      {photos.length > 1 && (
        <div className="galerie__vignettes">
          {photos.map((p, index) => (
            <button
              key={p.id}
              type="button"
              className={`galerie__vignette${p.id === affichee.id ? ' galerie__vignette--active' : ''}`}
              onClick={() => setSelectionId(p.id)}
              aria-label={`Voir la photo ${index + 1}`}
            >
              <img src={p.url} alt="" />
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
