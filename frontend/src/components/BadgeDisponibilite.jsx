import { libelleDisponibilite } from '../utils/produit.js'

export default function BadgeDisponibilite({ disponibilite }) {
  return <span className={`badge badge--${disponibilite}`}>{libelleDisponibilite(disponibilite)}</span>
}
