import { Link } from 'react-router-dom'
import BadgeDisponibilite from './BadgeDisponibilite.jsx'
import { photoPrincipale, prixAffiche } from '../utils/produit.js'

export default function CarteProduit({ produit }) {
  const photo = photoPrincipale(produit.photos)
  return (
    <article className="carte">
      <Link to={`/produits/${produit.id}`} className="carte__lien">
        {photo
          ? <img src={photo.url} alt={produit.nom} className="carte__photo" loading="lazy" />
          : <div className="photo-vide">Photo à venir</div>}
        <div className="carte__infos">
          <h2 className="carte__nom">{produit.nom}</h2>
          <p className="carte__prix">{prixAffiche(produit)}</p>
          <BadgeDisponibilite disponibilite={produit.disponibilite} />
        </div>
      </Link>
    </article>
  )
}
