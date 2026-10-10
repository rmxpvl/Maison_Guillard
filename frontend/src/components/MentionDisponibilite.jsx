import { libelleDisponibilite } from '../utils/produit.js'

// Discreet text mention; nothing is shown for an available piece.
export default function MentionDisponibilite({ disponibilite }) {
  if (disponibilite === 'disponible') return null
  return <span className="mention-dispo">{libelleDisponibilite(disponibilite)}</span>
}
