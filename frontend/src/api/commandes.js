import { apiPost } from './client.js'

export function creerCommande(commande) {
  return apiPost('/commandes', commande)
}
