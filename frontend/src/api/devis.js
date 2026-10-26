import { apiPost } from './client.js'

export function creerDevis(demande) {
  return apiPost('/devis', demande)
}
