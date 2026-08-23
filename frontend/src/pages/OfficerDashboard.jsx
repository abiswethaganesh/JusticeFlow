import { useEffect, useState } from 'react'
import StatusBadge from '../components/StatusBadge'
import FIRDraftViewer from '../components/FIRDraftViewer'
import {
  fetchComplaintsApi,
  updateComplaintStatusApi,
  fetchCaseEventsApi,
  fetchCaseEvidenceApi,
  fetchFIRDraftApi,
  getErrorMessage,
} from '../services/api'
import { useAuth } from '../context/AuthContext'
import { FORM_SCHEMAS } from '../data/formSchemas'

const TYPE_LABELS = {
  vehicle_theft: 'Vehicle Theft',
  cyber_fraud: 'Cyber Fraud',
  missing_person: 'Missing Person',
  property_theft: 'Property Theft',
  assault: 'Physical Assault',
  threat: 'Threat / Intimidation',
  harassment: 'Harassment',
  lost_document: 'Lost Document',
  other: 'General Complaint',
}

const ALL_STATUSES = [
  'SUBMITTED',
  'UNDER_REVIEW',
  'INFORMATION_REQUIRED',
  'ASSIGNED',
  'INVESTIGATION',
  'ACTION_TAKEN',
  'RESOLVED',
  'CLOSED',
  'REJECTED',
]

function formatDate(isoString) {
  try {
    return new Date(isoString).toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return isoString
  }
}

function OfficerCaseDetail({ caseItem, onBack, onStatusUpdated }) {
  const [currentStatus, setCurrentStatus] = useState(caseItem.status)
  const [remarks, setRemarks] = useState('')
  const [updating, setUpdating] = useState(false)
  const [updateError, setUpdateError] = useState(null)
  const [successMsg, setSuccessMsg] = useState(null)

  // Sub-data state
  const [events, setEvents] = useState([])
  const [evidenceList, setEvidenceList] = useState([])
  const [firDraft, setFirDraft] = useState(null)
  const [loadingSubData, setLoadingSubData] = useState(true)

  useEffect(() => {
    async function loadSubData() {
      setLoadingSubData(true)
      try {
        const [evs, evids] = await Promise.all([
          fetchCaseEventsApi(caseItem.case_id),
          fetchCaseEvidenceApi(caseItem.case_id),
        ])
        setEvents(evs)
        setEvidenceList(evids)

        if (caseItem.is_cognizable) {
          try {
            const draft = await fetchFIRDraftApi(caseItem.case_id)
            setFirDraft(draft)
          } catch (e) {
            // FIR draft fail fallback
          }
        }
      } catch (err) {
        // ignore error
      } finally {
        setLoadingSubData(false)
      }
    }
    loadSubData()
  }, [caseItem.case_id, caseItem.is_cognizable])

  const handleStatusChange = async (newStatus) => {
    setUpdating(true)
    setUpdateError(null)
    setSuccessMsg(null)
    try {
      const updated = await updateComplaintStatusApi(caseItem.case_id, newStatus, remarks)
      setCurrentStatus(updated.status)
      setSuccessMsg(`Status updated to ${newStatus}. Recorded in PostgreSQL case_events.`)
      setRemarks('')

      // Reload events timeline
      const freshEvents = await fetchCaseEventsApi(caseItem.case_id)
      setEvents(freshEvents)

      if (onStatusUpdated) onStatusUpdated(updated)
    } catch (err) {
      setUpdateError(getErrorMessage(err, 'Failed to update case status.'))
    } finally {
      setUpdating(false)
    }
  }

  const structured = caseItem.structured_data || {}
  const location =
    caseItem.incident_details?.location ||
    structured.incident_location ||
    structured.last_seen_location ||
    structured.property_location ||
    'Location not specified'

  return (
    <div className="card card-pad">
      <button className="btn btn-ghost" style={{ padding: 0, marginBottom: '1rem' }} onClick={onBack}>
        ← Back to Station Register
      </button>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <span className="eyebrow">Officer Case Inspection</span>
          <h2 style={{ fontSize: '1.3rem' }}>
            <span className="case-id-mono">{caseItem.case_id}</span> — {TYPE_LABELS[caseItem.complaint_type] || caseItem.complaint_type}
          </h2>
          <div style={{ display: 'flex', gap: '0.4rem', marginTop: '0.3rem' }}>
            <span
              style={{
                background: caseItem.is_cognizable ? '#fef2f2' : '#f0fdf4',
                color: caseItem.is_cognizable ? '#991b1b' : '#166534',
                fontSize: '0.75rem',
                fontWeight: 700,
                padding: '0.15rem 0.5rem',
                borderRadius: '4px',
              }}
            >
              {caseItem.is_cognizable ? 'Cognizable Offense' : 'Non-Cognizable'}
            </span>
            <span
              style={{
                background: '#e0e7ff',
                color: '#3730a3',
                fontSize: '0.75rem',
                fontWeight: 700,
                padding: '0.15rem 0.5rem',
                borderRadius: '4px',
              }}
            >
              Priority: {caseItem.priority || 'MEDIUM'}
            </span>
          </div>
        </div>
        <div>
          <StatusBadge status={currentStatus} />
        </div>
      </div>

      <hr className="section-divider" />

      {/* Case Overview Grid */}
      <div className="entity-grid" style={{ marginBottom: '1.25rem' }}>
        <div className="entity-item">
          <div className="entity-item-label">Incident Location</div>
          <div className="entity-item-value">{location}</div>
        </div>
        <div className="entity-item">
          <div className="entity-item-label">Assigned Station Branch</div>
          <div className="entity-item-value">{caseItem.assigned_station}</div>
        </div>
        <div className="entity-item">
          <div className="entity-item-label">Submitted Date</div>
          <div className="entity-item-value">{formatDate(caseItem.created_at)}</div>
        </div>
        <div className="entity-item">
          <div className="entity-item-label">Complainant Phone</div>
          <div className="entity-item-value">{caseItem.citizen_phone || '—'}</div>
        </div>
      </div>

      {/* Status Management Module */}
      <div
        style={{
          background: 'var(--color-bg-subtle, #f8fafc)',
          padding: '1rem',
          borderRadius: '8px',
          border: '1px solid var(--color-border)',
          marginBottom: '1.25rem',
        }}
      >
        <span className="eyebrow" style={{ marginBottom: '0.4rem' }}>
          Official Status Update & Case Audit Logging
        </span>

        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', margin: '0.5rem 0' }}>
          {ALL_STATUSES.map((st) => (
            <button
              key={st}
              className={`btn ${currentStatus === st ? 'btn-primary' : 'btn-ghost'}`}
              style={{ fontSize: '0.78rem', padding: '0.35rem 0.65rem' }}
              disabled={updating || currentStatus === st}
              onClick={() => handleStatusChange(st)}
            >
              {st.replace(/_/g, ' ')}
            </button>
          ))}
        </div>

        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
          <input
            type="text"
            placeholder="Official remarks / notes for status change (optional)..."
            value={remarks}
            onChange={(e) => setRemarks(e.target.value)}
            style={{ flex: 1, padding: '0.45rem 0.65rem', fontSize: '0.85rem', borderRadius: '6px', border: '1px solid var(--color-border)' }}
          />
        </div>

        {updateError && <div className="error-banner" style={{ marginTop: '0.75rem' }}>{updateError}</div>}
        {successMsg && (
          <div style={{ marginTop: '0.75rem', color: 'var(--color-success, #16a34a)', fontSize: '0.85rem', fontWeight: 600 }}>
            ✓ {successMsg}
          </div>
        )}
      </div>

      {/* Case Summary */}
      {caseItem.summary && (
        <div style={{ marginBottom: '1.25rem' }}>
          <span className="eyebrow">AI Executive Case Summary</span>
          <p className="summary-quote">{caseItem.summary}</p>
        </div>
      )}

      {/* Extracted Entities */}
      {Object.keys(structured).length > 0 && (
        <div style={{ marginBottom: '1.25rem' }}>
          <span className="eyebrow">Extracted Entities & Case Data</span>
          <div className="entity-grid" style={{ marginTop: '0.4rem' }}>
            {Object.entries(structured).map(([key, val]) => (
              <div className="entity-item" key={key}>
                <div className="entity-item-label">{key.replace(/_/g, ' ').toUpperCase()}</div>
                <div className="entity-item-value">{String(val || '—')}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Attached Evidence Files */}
      {evidenceList.length > 0 && (
        <div style={{ marginBottom: '1.25rem' }}>
          <span className="eyebrow">Uploaded Case Evidence</span>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', marginTop: '0.4rem' }}>
            {evidenceList.map((ev) => (
              <div
                key={ev.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  background: 'white',
                  padding: '0.55rem 0.75rem',
                  borderRadius: '6px',
                  border: '1px solid var(--color-border)',
                  fontSize: '0.85rem',
                }}
              >
                <div>
                  <strong>{ev.title}</strong> ({ev.evidence_type})
                </div>
                <a href={ev.file_url} target="_blank" rel="noreferrer" style={{ color: 'var(--color-primary)', fontWeight: 600 }}>
                  View Evidence ↗
                </a>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Original Complaint Statement */}
      <div style={{ marginBottom: '1.5rem' }}>
        <span className="eyebrow">Original Citizen Complaint Statement</span>
        <div
          style={{
            background: '#f8fafc',
            padding: '0.9rem',
            borderRadius: '8px',
            border: '1px solid var(--color-border)',
            fontSize: '0.9rem',
            whiteSpace: 'pre-wrap',
            lineHeight: 1.5,
          }}
        >
          {caseItem.original_complaint || caseItem.complaint_text}
        </div>
      </div>

      {/* Case Events / Status History Timeline */}
      {events.length > 0 && (
        <div style={{ marginBottom: '1.5rem' }}>
          <span className="eyebrow">Audit Trail — Status & Event History</span>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.4rem' }}>
            {events.map((ev) => (
              <div
                key={ev.id}
                style={{
                  background: 'white',
                  padding: '0.6rem 0.8rem',
                  borderRadius: '6px',
                  border: '1px solid var(--color-border)',
                  fontSize: '0.82rem',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--color-text-muted)' }}>
                  <span>
                    <strong>{ev.actor_name}</strong> ({ev.actor_role})
                  </span>
                  <span>{formatDate(ev.created_at)}</span>
                </div>
                <div style={{ marginTop: '0.2rem', fontWeight: 600 }}>
                  Status: {ev.previous_status ? `${ev.previous_status} → ` : ''}
                  <span style={{ color: 'var(--color-primary)' }}>{ev.new_status}</span>
                </div>
                {ev.remarks && <div style={{ marginTop: '0.15rem', color: '#475569' }}>Note: {ev.remarks}</div>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* FIR Draft & CCTNS Module for Cognizable Cases */}
      {caseItem.is_cognizable && firDraft && (
        <FIRDraftViewer
          caseId={caseItem.case_id}
          initialFIRDraft={firDraft}
          onFIRRegistered={() => {
            handleStatusChange('INVESTIGATION')
          }}
        />
      )}
    </div>
  )
}

export default function OfficerDashboard() {
  const { user } = useAuth()
  const [complaints, setComplaints] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedCase, setSelectedCase] = useState(null)

  const loadStationCases = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchComplaintsApi()
      setComplaints(data)
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to load police station complaints.'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadStationCases()
  }, [])

  const pendingCount = complaints.filter((c) => c.status === 'SUBMITTED').length
  const investigationCount = complaints.filter(
    (c) => c.status === 'UNDER_REVIEW' || c.status === 'ASSIGNED' || c.status === 'INVESTIGATION'
  ).length
  const resolvedCount = complaints.filter((c) => c.status === 'RESOLVED' || c.status === 'CLOSED').length

  const handleCaseUpdated = (updatedCase) => {
    setComplaints((prev) => prev.map((c) => (c.case_id === updatedCase.case_id ? updatedCase : c)))
  }

  return (
    <>
      <div className="page-header">
        <h1>Officer Dashboard — {user?.station_branch || 'Police Station'}</h1>
        <p>
          Officer <strong>{user?.full_name}</strong> ({user?.officer_id || 'Officer'}). Showing complaints assigned strictly to your police station ID.
        </p>
      </div>

      {selectedCase ? (
        <OfficerCaseDetail
          caseItem={selectedCase}
          onBack={() => setSelectedCase(null)}
          onStatusUpdated={handleCaseUpdated}
        />
      ) : (
        <>
          <div className="stat-grid">
            <div className="card stat-card">
              <div className="stat-value">{loading ? '—' : complaints.length}</div>
              <div className="stat-label">Station Complaints</div>
            </div>
            <div className="card stat-card">
              <div className="stat-value">{loading ? '—' : pendingCount}</div>
              <div className="stat-label">Pending Review</div>
            </div>
            <div className="card stat-card">
              <div className="stat-value">{loading ? '—' : investigationCount}</div>
              <div className="stat-label">In Investigation</div>
            </div>
            <div className="card stat-card">
              <div className="stat-value">{loading ? '—' : resolvedCount}</div>
              <div className="stat-label">Resolved / Closed</div>
            </div>
          </div>

          <div className="card">
            <div
              className="card-pad"
              style={{ paddingBottom: '0.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
            >
              <h2 style={{ fontSize: '1.05rem' }}>Station Complaint Register (PostgreSQL)</h2>
              <button className="btn btn-ghost" style={{ fontSize: '0.8rem' }} onClick={loadStationCases}>
                ↻ Refresh Cases
              </button>
            </div>

            {loading && (
              <p style={{ padding: '0 1.1rem 1.1rem', color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>
                Loading station cases…
              </p>
            )}

            {!loading && error && <div className="error-banner" style={{ margin: '0 1.1rem 1.1rem' }}>{error}</div>}

            {!loading && !error && complaints.length === 0 && (
              <div style={{ padding: '1rem 1.1rem 1.5rem', color: 'var(--color-text-muted)' }}>
                No complaints assigned to {user?.station_branch || 'your police station branch'}.
              </div>
            )}

            {!loading && !error && complaints.length > 0 && (
              <div style={{ padding: '0 0.5rem 0.5rem' }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Case ID</th>
                      <th>Complaint Type</th>
                      <th>Incident Location</th>
                      <th>Assigned Branch</th>
                      <th>Date</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {complaints.map((c) => {
                      const loc =
                        c.incident_details?.location ||
                        c.structured_data?.incident_location ||
                        c.structured_data?.last_seen_location ||
                        '—'
                      return (
                        <tr
                          key={c.case_id}
                          className="clickable"
                          onClick={() => setSelectedCase(c)}
                          tabIndex={0}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') setSelectedCase(c)
                          }}
                        >
                          <td data-label="Case ID">
                            <span className="case-id-mono">{c.case_id}</span>
                          </td>
                          <td data-label="Type">{TYPE_LABELS[c.complaint_type] || c.complaint_type}</td>
                          <td data-label="Location">{loc}</td>
                          <td data-label="Branch">{c.assigned_station}</td>
                          <td data-label="Date">{formatDate(c.created_at)}</td>
                          <td data-label="Status">
                            <StatusBadge status={c.status} />
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </>
  )
}
