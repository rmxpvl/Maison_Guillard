import { apiGet } from './client.js'

export function getCategories() {
  return apiGet('/categories')
}
