import { apiGet } from './client.js'

export function getProduits({ categorie = null, disponibilite = null } = {}) {
  const params = new URLSearchParams()
  if (categorie !== null) params.set('categorie', categorie)
  if (disponibilite !== null) params.set('disponibilite', disponibilite)
  const query = params.toString()
  return apiGet(`/produits${query ? `?${query}` : ''}`)
}

export function getProduit(id) {
  return apiGet(`/produits/${id}`)
}
