import { STATUTS_DEMANDE, libelleStatut, tonStatut } from '../../utils/admin.js'

// Status of a request as a coloured pill: the colour says at a glance whether it needs action.
export default function BadgeStatut({ statut }) {
  return <span className={`badge badge--${tonStatut(statut)}`}>{libelleStatut(STATUTS_DEMANDE, statut)}</span>
}
