import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getDocument } from '../api.js'
import { statusLabel } from '../status.js'

const FINISHED = new Set(['completed', 'failed'])

export default function DocumentPage() {
  const { id } = useParams()
  const [document, setDocument] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let timer
    let cancelled = false

    async function load() {
      try {
        const next = await getDocument(id)
        if (cancelled) return
        setDocument(next)
        setError('')
        if (!FINISHED.has(next.status)) {
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
  }, [id])

  const fields = document?.extracted_fields
    ? Object.entries(document.extracted_fields)
    : []
  const missing = document?.missing_fields ?? []
  const report = document?.report

  return (
    <>
      <p>
        <Link to="/">Documents</Link>
      </p>
      {error && <p className="error">{error}</p>}
      {!document && !error && <p>Loading…</p>}
      {document && (
        <>
          <h1>{document.filename}</h1>
          <p>Status: {statusLabel(document.status)}</p>
          {document.document_type && <p>Type: {document.document_type}</p>}
          {(document.status === 'failed' || document.status === 'retrying') &&
            document.error_message && (
              <p className="error">{document.error_message}</p>
            )}
          {fields.length > 0 && (
            <section>
              <h2>Extracted fields</h2>
              <dl>
                {fields.map(([name, value]) => (
                  <div key={name}>
                    <dt>{label(name)}</dt>
                    <dd>{value || '—'}</dd>
                  </div>
                ))}
              </dl>
            </section>
          )}
          {missing.length > 0 && (
            <section>
              <h2>Missing fields</h2>
              <ul>
                {missing.map((name) => (
                  <li key={name}>{label(name)}</li>
                ))}
              </ul>
            </section>
          )}
          {report && (
            <section>
              <h2>Report</h2>
              {typeof report === 'string' ? (
                <p>{report}</p>
              ) : (
                Object.entries(report).map(([name, value]) => (
                  <p key={name}>
                    <strong>{label(name)}: </strong>
                    {String(value ?? '')}
                  </p>
                ))
              )}
            </section>
          )}
        </>
      )}
    </>
  )
}

function label(name) {
  return name.replaceAll('_', ' ')
}
