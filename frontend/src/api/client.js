export class ApiError extends Error {
  constructor(status, message) {
    super(message)
    this.status = status
  }
}

export async function apiGet(path) {
  const res = await fetch(`/api${path}`)
  if (!res.ok) {
    throw new ApiError(res.status, `Erreur API ${res.status}`)
  }
  return res.json()
}
