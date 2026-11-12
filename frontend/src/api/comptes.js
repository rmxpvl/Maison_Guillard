import { apiPost } from './client.js'

export function inscription(email) {
  return apiPost('/clients/inscription', { email })
}

export function activerCompte(token, motDePasse) {
  return apiPost('/clients/activer', { token, mot_de_passe: motDePasse })
}

export function motDePasseOublie(email) {
  return apiPost('/clients/mot-de-passe-oublie', { email })
}

export function reinitialiserMotDePasse(token, motDePasse) {
  return apiPost('/clients/reinitialiser', { token, mot_de_passe: motDePasse })
}
