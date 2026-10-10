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
      <img src={affichee.url} alt={nom} className="galerie__grande" />
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
