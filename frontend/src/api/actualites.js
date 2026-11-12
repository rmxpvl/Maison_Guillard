import { apiGet } from './client.js'

export function getActualites() {
  return apiGet('/actualites')
}

export function getActualite(slug) {
  return apiGet(`/actualites/${encodeURIComponent(slug)}`)
}
