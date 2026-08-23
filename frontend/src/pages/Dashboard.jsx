import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import ComplaintCard from '../components/ComplaintCard'
import { fetchComplaintsApi, deleteComplaintApi, getErrorMessage } from '../services/api'
import { useAuth } from '../context/AuthContext'

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

function formatDate(isoString) {
  try {
    return new Date(isoString).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
  } catch {
    return isoString
  }
}

function computeSummary(complaints) {
  return {
    total: complaints.length,
    pending: complaints.filter((c) => c.status === 'SUBMITTED').length,
    underReview: complaints.filter((c) => c.status === 'UNDER_REVIEW' || c.status === 'ASSIGNED' || c.status === 'INVESTIGATION').length,
    resolved: complaints.filter((c) => c.status === 'RESOLVED' || c.status === 'CLOSED').length,
  }
}

export default function Dashboard() {
  const { user } = useAuth()
  const [complaints, setComplaints] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [deleteSuccessMsg, setDeleteSuccessMsg] = useState(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const data = await fetchComplaintsApi()
        if (!cancelled) setComplaints(data)
      } catch (err) {
        if (!cancelled) setError(getErrorMessage(err, 'Unable to load your complaint history.'))
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [])

  const handleDeleteComplaint = async (caseId) => {
    setError(null)
    setDeleteSuccessMsg(null)
    try {
      await deleteComplaintApi(caseId)
      setComplaints((prev) => prev.filter((c) => c.case_id !== caseId))
      setDeleteSuccessMsg(`Complaint ${caseId} deleted successfully.`)
      setTimeout(() => setDeleteSuccessMsg(null), 4000)
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to delete complaint.'))
    }
  }

  const summary = computeSummary(complaints)

  return (
    <>
      <div className="page-header">
        <h1>Welcome back, {user?.full_name || 'Citizen'}</h1>
        <p>Lodge and track your criminal justice complaints through Conversational AI Intake.</p>
      </div>

      <div className="stat-grid">
        <div className="card stat-card">
          <div className="stat-value">{loading ? '—' : summary.total}</div>
          <div className="stat-label">Total Complaints</div>
        </div>
        <div className="card stat-card">
          <div className="stat-value">{loading ? '—' : summary.pending}</div>
          <div className="stat-label">Pending Review</div>
        </div>
        <div className="card stat-card">
          <div className="stat-value">{loading ? '—' : summary.underReview}</div>
          <div className="stat-label">In Investigation</div>
        </div>
        <div className="card stat-card">
          <div className="stat-value">{loading ? '—' : summary.resolved}</div>
          <div className="stat-label">Resolved / Closed</div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: '1.25rem' }}>
        <div
          className="card-pad"
          style={{ paddingBottom: '0.75rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
        >
          <h2 style={{ fontSize: '1.05rem' }}>Your Complaint History (PostgreSQL)</h2>
          <Link to="/intake" className="btn btn-primary" style={{ fontSize: '0.85rem' }}>
            Conversational AI Intake
          </Link>
        </div>

        {loading && (
          <p style={{ padding: '0 1.1rem 1.1rem', color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>
            Loading your registered cases…
          </p>
        )}

        {deleteSuccessMsg && (
          <div
            style={{
              margin: '0 1.1rem 1rem',
              padding: '0.75rem 1rem',
              background: '#f0fdf4',
              border: '1px solid #bbf7d0',
              color: '#166534',
              borderRadius: '6px',
              fontSize: '0.88rem',
              fontWeight: 600,
            }}
          >
            ✓ {deleteSuccessMsg}
          </div>
        )}

        {!loading && error && <div className="error-banner" style={{ margin: '0 1.1rem 1.1rem' }}>{error}</div>}

        {!loading && !error && complaints.length === 0 && (
          <div style={{ padding: '0.5rem 1.1rem 1.5rem' }}>
            <p style={{ color: 'var(--color-text-muted)', marginBottom: '1rem' }}>No complaints registered yet.</p>
            <Link to="/intake" className="btn btn-primary">
              Start Conversational AI Intake
            </Link>
          </div>
        )}

        {!loading &&
          !error &&
          complaints.map((c) => (
            <ComplaintCard
              key={c.case_id}
              complaint={{
                id: c.case_id,
                typeLabel: TYPE_LABELS[c.complaint_type] || c.complaint_type,
                status: c.status,
                date: formatDate(c.created_at),
              }}
              onDelete={handleDeleteComplaint}
            />
          ))}
      </div>

      {complaints.length > 0 && (
        <Link to="/intake" className="btn btn-primary">
          Start New Conversational AI Complaint Intake
        </Link>
      )}
    </>
  )
}
