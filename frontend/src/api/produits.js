import { apiGet } from './client.js'

export function getProduits({ univers = null, categorie = null } = {}) {
  const params = new URLSearchParams()
  if (univers !== null) params.set('univers', univers)
  if (categorie !== null) params.set('categorie', categorie)
  const query = params.toString()
  return apiGet(`/produits${query ? `?${query}` : ''}`)
}

export function getProduit(id) {
  return apiGet(`/produits/${id}`)
}
