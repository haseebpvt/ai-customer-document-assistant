import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { listDocuments, uploadDocument } from '../api.js'
import { statusLabel } from '../status.js'

const FINISHED = new Set(['completed', 'failed'])

export default function DocumentsPage() {
  const navigate = useNavigate()
  const [documents, setDocuments] = useState(null)
  const [error, setError] = useState('')
  const [uploading, setUploading] = useState(false)

  useEffect(() => {
    let timer
    let cancelled = false

    async function load() {
      try {
        const rows = sortNewest(await listDocuments())
        if (cancelled) return
        setDocuments(rows)
        setError('')
        if (rows.some((row) => !FINISHED.has(row.status))) {
          timer = setTimeout(load, 5000)
        }
      } catch (err) {
        if (!cancelled) setError(err.message)
      }
    }

    load()
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [])

  async function onSubmit(event) {
    event.preventDefault()
    const file = event.target.elements.file.files[0]
    if (!file) return
    setUploading(true)
    setError('')
    try {
      const created = await uploadDocument(file)
      navigate(`/documents/${created.id}`)
    } catch (err) {
      setError(err.message)
      setUploading(false)
    }
  }

  return (
    <>
      <h1>Documents</h1>
      <form onSubmit={onSubmit}>
        <input name="file" type="file" accept=".pdf,.docx,.jpg,.jpeg,.png,.gif,.webp" required />
        <button type="submit" disabled={uploading}>
          {uploading ? 'Uploading…' : 'Upload'}
        </button>
      </form>
      {error && <p className="error">{error}</p>}
      {documents === null && !error && <p>Loading…</p>}
      {documents?.length === 0 && <p>No documents yet.</p>}
      {documents?.length > 0 && (
        <ul className="documents">
          {documents.map((document) => (
            <li key={document.id}>
              <Link to={`/documents/${document.id}`}>{document.filename}</Link>
              <span>{statusLabel(document.status)}</span>
              <time>{formatTime(document.created_at)}</time>
              {document.status === 'failed' && document.error_message && (
                <span className="error">{document.error_message}</span>
              )}
            </li>
          ))}
        </ul>
      )}
    </>
  )
}

function sortNewest(documents) {
  return [...documents].sort(
    (a, b) => new Date(b.created_at) - new Date(a.created_at),
  )
}

function formatTime(value) {
  if (!value) return ''
  return new Date(value).toLocaleString()
}
