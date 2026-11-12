// Same-origin /api in development (Vite proxies it); the API's own address in production (VITE_API_URL).
export const API_BASE = (import.meta.env?.VITE_API_URL ?? '/api').replace(/\/$/, '')

export class ApiError extends Error {
  // detail: the API's French message when it sends one as a string, else null.
  constructor(status, message, detail = null) {
    super(message)
    this.status = status
    this.detail = detail
  }
}

export async function apiGet(path) {
  const res = await fetch(`${API_BASE}${path}`)
  if (!res.ok) {
    throw new ApiError(res.status, `Erreur API ${res.status}`)
  }
  return res.json()
}

// Any API call. `body` is sent as JSON, `formulaire` (a FormData) as multipart for file uploads,
// `token` as the admin's Bearer token, `blob` to get a file back instead of JSON. A 204 (nothing to send back) resolves to null.
export async function apiRequete(path, { method = 'GET', body, formulaire, token, blob = false } = {}) {
  const headers = {}
  if (token) headers.Authorization = `Bearer ${token}`
  let corps
  if (formulaire) {
    corps = formulaire // the browser sets the multipart Content-Type itself
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    corps = JSON.stringify(body)
  }

  const res = await fetch(`${API_BASE}${path}`, { method, headers, body: corps })
  if (res.status === 204) return null
  if (blob && res.ok) return res.blob() // a PDF, for instance
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    // Business errors send a string; Pydantic validation errors send a list.
    const detail = typeof data?.detail === 'string' ? data.detail : null
    throw new ApiError(res.status, `Erreur API ${res.status}`, detail)
  }
  return data
}

export function apiPost(path, body) {
  return apiRequete(path, { method: 'POST', body })
}
