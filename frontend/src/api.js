const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function request(path, options) {
  const response = await fetch(`${API}${path}`, options)
  if (!response.ok) {
    throw new Error(`Request failed (${response.status})`)
  }
  return response.json()
}

export function listDocuments() {
  return request('/documents')
}

export function getDocument(id) {
  return request(`/documents/${id}`)
}

export function uploadDocument(file) {
  const body = new FormData()
  body.append('file', file)
  return request('/documents', { method: 'POST', body })
}
