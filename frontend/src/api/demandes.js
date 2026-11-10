import { apiGet, apiPost } from './client.js'

export function creerDemande(demande) {
  return apiPost('/demandes', demande)
}

export function creerProjetLibre(projet) {
  return apiPost('/demandes/projet-libre', projet)
}

export function getSuiviDemande(jeton) {
  return apiGet(`/demandes/suivi/${encodeURIComponent(jeton)}`)
}
