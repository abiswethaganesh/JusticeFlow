import { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import CaseTimeline from '../components/CaseTimeline'
import StatusBadge from '../components/StatusBadge'
import EvidenceUploader from '../components/EvidenceUploader'
import { fetchComplaintApi, fetchCaseEventsApi, deleteComplaintApi, getErrorMessage } from '../services/api'
import { FORM_SCHEMAS } from '../data/formSchemas'

const STAGE_BY_STATUS = {
  SUBMITTED: 'submitted',
  UNDER_REVIEW: 'officer_review',
  INFORMATION_REQUIRED: 'officer_review',
  ASSIGNED: 'officer_review',
  INVESTIGATION: 'updated',
  ACTION_TAKEN: 'updated',
  RESOLVED: 'updated',
  CLOSED: 'updated',
  REJECTED: 'updated',
}

function formatDate(isoString) {
  if (!isoString) return ''
  try {
    return new Date(isoString).toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return String(isoString)
  }
}

export default function CaseStatus() {
  const { caseId } = useParams()
  const navigate = useNavigate()
  const [complaint, setComplaint] = useState(null)
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [deleting, setDeleting] = useState(false)
  const [showConfirmDelete, setShowConfirmDelete] = useState(false)

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const [cData, evData] = await Promise.all([
          fetchComplaintApi(caseId).catch(() => null),
          fetchCaseEventsApi(caseId).catch(() => []),
        ])

        if (!cancelled) {
          if (!cData) {
            setError(`No complaint found matching Case ID ${caseId} or access was denied.`)
          } else {
            setComplaint(cData)
            setEvents(Array.isArray(evData) ? evData : [])
          }
        }
      } catch (err) {
        if (!cancelled) setError(getErrorMessage(err, `Unable to load case ${caseId}.`))
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [caseId])

  const handleDelete = async () => {
    setDeleting(true)
    try {
      await deleteComplaintApi(caseId)
      navigate('/', { replace: true })
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to delete complaint.'))
      setDeleting(false)
      setShowConfirmDelete(false)
    }
  }

  const schema = complaint ? FORM_SCHEMAS[complaint.complaint_type] || FORM_SCHEMAS.other : null
  const formattedType = complaint?.complaint_type ? complaint.complaint_type.replace(/_/g, ' ').toUpperCase() : 'GENERAL'

  return (
    <>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <Link to="/" style={{ fontSize: '0.85rem', color: 'var(--color-primary)', textDecoration: 'none', display: 'inline-block', marginBottom: '0.4rem', fontWeight: 600 }}>
            ← Back to Dashboard
          </Link>
          <h1 style={{ margin: 0 }}>Case Status & Tracking</h1>
          <p style={{ marginTop: '0.25rem' }}>
            Official complaint record <span className="case-id-mono">#{caseId}</span> in JusticeFlow PostgreSQL Database.
          </p>
        </div>

        {complaint && (
          <div>
            {showConfirmDelete ? (
              <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                <button
                  className="btn"
                  onClick={handleDelete}
                  disabled={deleting}
                  style={{ background: '#dc2626', color: 'white', border: 'none', fontSize: '0.85rem', fontWeight: 600 }}
                >
                  {deleting ? 'Deleting…' : 'Confirm Delete'}
                </button>
                <button className="btn btn-ghost" onClick={() => setShowConfirmDelete(false)} disabled={deleting} style={{ fontSize: '0.85rem' }}>
                  Cancel
                </button>
              </div>
            ) : (
              <button
                className="btn btn-ghost"
                onClick={() => setShowConfirmDelete(true)}
                style={{ color: '#dc2626', borderColor: '#fca5a5', background: '#fef2f2', fontSize: '0.85rem', fontWeight: 600 }}
              >
                Delete Complaint
              </button>
            )}
          </div>
        )}
      </div>

      {loading && (
        <div className="card card-pad">
          <p style={{ color: 'var(--color-text-muted)' }}>Loading complaint details, station assignment, and status timeline…</p>
        </div>
      )}

      {!loading && error && (
        <div className="card card-pad">
          <div className="error-banner" style={{ marginTop: 0 }}>
            {error}
          </div>
          <div style={{ marginTop: '1rem' }}>
            <Link to="/" className="btn btn-primary" style={{ fontSize: '0.88rem' }}>
              Return to Dashboard
            </Link>
          </div>
        </div>
      )}

      {!loading && !error && complaint && (
        <>
          <div className="card card-pad" style={{ marginBottom: '1.25rem' }}>
            <div className="entity-grid">
              <div className="entity-item">
                <div className="entity-item-label">Case Reference ID</div>
                <div className="entity-item-value case-id-mono">{complaint.case_id}</div>
              </div>
              <div className="entity-item">
                <div className="entity-item-label">Complaint Classification</div>
                <div className="entity-item-value" style={{ fontWeight: 600 }}>{schema?.title || formattedType}</div>
              </div>
              <div className="entity-item">
                <div className="entity-item-label">Assigned Police Station</div>
                <div className="entity-item-value" style={{ fontWeight: 600, color: 'var(--color-primary)' }}>
                  📍 {complaint.assigned_station || 'Jurisdiction Police Station'}
                </div>
              </div>
              <div className="entity-item">
                <div className="entity-item-label">Current Status</div>
                <div className="entity-item-value">
                  <StatusBadge status={complaint.status} />
                </div>
              </div>
            </div>

            {complaint.summary && (
              <>
                <hr className="section-divider" />
                <span className="eyebrow">AI Executive Summary</span>
                <p className="summary-quote">{complaint.summary}</p>
              </>
            )}

            {complaint.structured_data && Object.keys(complaint.structured_data).length > 0 && (
              <>
                <hr className="section-divider" />
                <span className="eyebrow">Extracted Incident Information</span>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '0.75rem', marginTop: '0.5rem' }}>
                  {Object.entries(complaint.structured_data).map(([key, val]) => (
                    <div key={key} style={{ background: '#f8fafc', padding: '0.5rem 0.75rem', borderRadius: '6px', border: '1px solid var(--color-border)' }}>
                      <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
                        {key.replace(/_/g, ' ')}
                      </div>
                      <div style={{ fontSize: '0.88rem', fontWeight: 600, marginTop: '0.1rem' }}>
                        {val ? String(val) : '—'}
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}

            {complaint.complaint_text && (
              <>
                <hr className="section-divider" />
                <span className="eyebrow">Original Complaint Statement</span>
                <p style={{ fontSize: '0.9rem', lineHeight: 1.5, background: '#f1f5f9', padding: '0.85rem 1rem', borderRadius: '8px', color: 'var(--color-text-main)', marginTop: '0.4rem' }}>
                  {complaint.complaint_text}
                </p>
              </>
            )}
          </div>

          {/* Progress Timeline */}
          <div className="card card-pad" style={{ marginBottom: '1.25rem' }}>
            <span className="eyebrow">Investigation Progress Timeline</span>
            <div style={{ marginTop: '0.75rem' }}>
              <CaseTimeline
                currentStage={STAGE_BY_STATUS[complaint.status] || 'submitted'}
                submittedAt={formatDate(complaint.created_at)}
              />
            </div>
          </div>

          {/* Evidence Management Section */}
          <div style={{ marginBottom: '1.25rem' }}>
            <EvidenceUploader caseId={complaint.case_id} />
          </div>

          {/* Audit Event History */}
          {events && events.length > 0 && (
            <div className="card card-pad">
              <span className="eyebrow">Official Police Case Log (PostgreSQL Status History)</span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', marginTop: '0.5rem' }}>
                {events.map((ev) => (
                  <div
                    key={ev.id}
                    style={{
                      background: '#f8fafc',
                      padding: '0.75rem 1rem',
                      borderRadius: '8px',
                      border: '1px solid var(--color-border)',
                      fontSize: '0.88rem',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--color-text-muted)', fontSize: '0.8rem' }}>
                      <span>
                        👤 <strong>{ev.actor_name}</strong> ({ev.actor_role})
                      </span>
                      <span>{formatDate(ev.created_at)}</span>
                    </div>
                    <div style={{ marginTop: '0.25rem', fontWeight: 600 }}>
                      Status: {ev.previous_status ? `${ev.previous_status} → ` : ''}
                      <span style={{ color: 'var(--color-primary)' }}>{ev.new_status}</span>
                    </div>
                    {ev.remarks && <div style={{ marginTop: '0.2rem', color: '#475569' }}>{ev.remarks}</div>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </>
  )
}
