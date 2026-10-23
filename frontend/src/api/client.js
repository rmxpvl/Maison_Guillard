export class ApiError extends Error {
  // detail: the API's French message when it sends one as a string, else null.
  constructor(status, message, detail = null) {
    super(message)
    this.status = status
    this.detail = detail
  }
}

export async function apiGet(path) {
  const res = await fetch(`/api${path}`)
  if (!res.ok) {
    throw new ApiError(res.status, `Erreur API ${res.status}`)
  }
  return res.json()
}

export async function apiPost(path, body) {
  const res = await fetch(`/api${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    // Business errors send a string; Pydantic validation errors send a list.
    const detail = typeof data?.detail === 'string' ? data.detail : null
    throw new ApiError(res.status, `Erreur API ${res.status}`, detail)
  }
  return data
}
