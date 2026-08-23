import { useState, useEffect } from 'react'
import { uploadEvidenceApi, deleteEvidenceApi, fetchCaseEvidenceApi, getErrorMessage } from '../services/api'

export default function EvidenceUploader({ caseId, recommendedEvidence = [], onEvidenceUploaded }) {
  const [uploading, setUploading] = useState(false)
  const [deletingId, setDeletingId] = useState(null)
  const [error, setError] = useState(null)
  const [uploadedList, setUploadedList] = useState([])
  const [evidenceType] = useState('document')
  const [title, setTitle] = useState('')

  useEffect(() => {
    if (caseId && caseId !== 'DRAFT') {
      fetchCaseEvidenceApi(caseId)
        .then((evList) => {
          if (Array.isArray(evList)) setUploadedList(evList)
        })
        .catch(() => {})
    }
  }, [caseId])

  const handleFileChange = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    setUploading(true)
    setError(null)
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('case_id', caseId || 'DRAFT')
      formData.append('evidence_type', evidenceType)
      formData.append('title', title || file.name)

      let res
      if (caseId && caseId !== 'DRAFT') {
        res = await uploadEvidenceApi(formData)
      } else {
        res = {
          id: Date.now(),
          case_id: 'DRAFT',
          evidence_type: evidenceType,
          title: title || file.name,
          file_name: file.name,
          file_path: file.name,
          file_url: URL.createObjectURL(file),
          uploaded_at: new Date().toISOString(),
        }
      }

      setUploadedList((prev) => [...prev, res])
      if (onEvidenceUploaded) onEvidenceUploaded(res)
      setTitle('')
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to upload evidence file.'))
    } finally {
      setUploading(false)
    }
  }

  const handleDeleteEvidence = async (evId) => {
    setDeletingId(evId)
    setError(null)
    try {
      if (typeof evId === 'number' && evId < 1000000000000) {
        await deleteEvidenceApi(evId)
      }
      setUploadedList((prev) => prev.filter((item) => item.id !== evId))
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to delete evidence.'))
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div className="card card-pad" style={{ marginTop: '1rem', background: 'var(--color-bg-subtle, #f8fafc)' }}>
      <span className="eyebrow" style={{ marginBottom: '0.4rem' }}>
        Evidence Collection
      </span>
      <h3 style={{ fontSize: '1rem', marginBottom: '0.75rem' }}>Supporting Evidence Documents & Media</h3>

      {recommendedEvidence.length > 0 && (
        <div style={{ marginBottom: '1rem' }}>
          <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '0.4rem' }}>
            Recommended Evidence Items to Upload:
          </div>
          <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
            {recommendedEvidence.map((item, idx) => (
              <span
                key={idx}
                style={{
                  background: 'white',
                  border: '1px solid var(--color-border)',
                  borderRadius: '6px',
                  padding: '0.3rem 0.6rem',
                  fontSize: '0.8rem',
                  color: 'var(--color-primary)',
                  fontWeight: 500,
                }}
              >
                {item}
              </span>
            ))}
          </div>
        </div>
      )}

      {error && <div className="error-banner" style={{ marginBottom: '0.75rem' }}>{error}</div>}

      <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <input
          type="text"
          placeholder="Evidence Document Title (optional)"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          style={{
            flex: 1,
            minWidth: '200px',
            padding: '0.55rem 0.75rem',
            borderRadius: '6px',
            border: '1px solid var(--color-border)',
            fontSize: '0.88rem',
          }}
        />
        <label
          className="btn btn-primary"
          style={{ cursor: uploading ? 'wait' : 'pointer', fontSize: '0.85rem', margin: 0 }}
        >
          {uploading ? 'Uploading…' : 'Upload Evidence File'}
          <input type="file" onChange={handleFileChange} style={{ display: 'none' }} disabled={uploading} />
        </label>
      </div>

      {uploadedList.length > 0 && (
        <div style={{ marginTop: '1rem' }}>
          <div style={{ fontSize: '0.82rem', fontWeight: 600, marginBottom: '0.4rem' }}>Uploaded Files:</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            {uploadedList.map((item) => (
              <div
                key={item.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  background: 'white',
                  padding: '0.5rem 0.75rem',
                  borderRadius: '6px',
                  border: '1px solid var(--color-border)',
                  fontSize: '0.85rem',
                }}
              >
                <div>
                  <strong>{item.title}</strong>{' '}
                  <span style={{ color: 'var(--color-text-muted)', fontSize: '0.78rem' }}>({item.evidence_type})</span>
                </div>
                <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center' }}>
                  {item.file_url && (
                    <a
                      href={item.file_url}
                      target="_blank"
                      rel="noreferrer"
                      style={{ color: 'var(--color-primary)', fontSize: '0.8rem', textDecoration: 'none', fontWeight: 600 }}
                    >
                      View File ↗
                    </a>
                  )}
                  <button
                    onClick={() => handleDeleteEvidence(item.id)}
                    disabled={deletingId === item.id}
                    style={{
                      background: '#fef2f2',
                      color: '#dc2626',
                      border: '1px solid #fca5a5',
                      borderRadius: '4px',
                      padding: '0.2rem 0.5rem',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    {deletingId === item.id ? 'Deleting…' : 'Delete'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
