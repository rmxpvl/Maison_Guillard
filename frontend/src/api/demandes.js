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

export function refuserDevis(jeton) {
  return apiPost(`/demandes/suivi/${encodeURIComponent(jeton)}/refuser`)
}

export function payerDevis(jeton) {
  return apiPost(`/demandes/suivi/${encodeURIComponent(jeton)}/payer`, { cgv_acceptees: true })
}

export function annulerCommande(jeton) {
  return apiPost(`/demandes/suivi/${encodeURIComponent(jeton)}/annuler`)
}

export function getMessagesDemande(jeton) {
  return apiGet(`/demandes/suivi/${encodeURIComponent(jeton)}/messages`)
}

export function envoyerMessageDemande(jeton, texte) {
  return apiPost(`/demandes/suivi/${encodeURIComponent(jeton)}/messages`, { texte })
}
