import React, { useEffect, useState } from 'react'
import { fetchEvidenceAuditTrailApi } from '../services/api'

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

export default function EvidenceTimeline({ evidenceId }) {
  const [trail, setTrail] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadTrail() {
      if (!evidenceId) return
      setLoading(true)
      try {
        const events = await fetchEvidenceAuditTrailApi(evidenceId)
        setTrail(events)
      } catch (err) {
        // ignore error
      } finally {
        setLoading(false)
      }
    }
    loadTrail()
  }, [evidenceId])

  if (loading) return <p style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)' }}>Loading evidence audit trail…</p>
  if (trail.length === 0) return <p style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)' }}>No audit events recorded yet.</p>

  // Find Time-to-Preservation-Request metric if present
  const preservationEvent = trail.find((e) => e.time_to_preservation_minutes != null)

  return (
    <div style={{ marginTop: '0.5rem' }}>
      {preservationEvent && (
        <div
          style={{
            background: '#ecfdf5',
            border: '1px solid #a7f3d0',
            color: '#065f46',
            padding: '0.55rem 0.75rem',
            borderRadius: '6px',
            fontSize: '0.8rem',
            fontWeight: 600,
            marginBottom: '0.75rem',
            display: 'flex',
            justify: 'space-between',
            alignItems: 'center',
          }}
        >
          <span>⏱ Evaluation Metric — Time-to-Preservation-Request:</span>
          <span style={{ background: '#10b981', color: 'white', padding: '0.15rem 0.45rem', borderRadius: '4px' }}>
            {preservationEvent.time_to_preservation_minutes < 60
              ? `${preservationEvent.time_to_preservation_minutes} mins`
              : `${(preservationEvent.time_to_preservation_minutes / 60.0).toFixed(1)} hrs`}
          </span>
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
        {trail.map((ev) => (
          <div
            key={ev.id}
            style={{
              background: '#f8fafc',
              padding: '0.5rem 0.65rem',
              borderRadius: '6px',
              border: '1px solid var(--color-border)',
              fontSize: '0.8rem',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--color-text-muted)' }}>
              <span>
                <strong>{ev.actor_name}</strong> ({ev.actor_role})
              </span>
              <span>{formatDate(ev.created_at)}</span>
            </div>
            <div style={{ marginTop: '0.15rem', fontWeight: 600, color: '#1e293b' }}>
              Action: <span style={{ color: 'var(--color-primary)' }}>{ev.action}</span>
              {ev.new_status && ` → Status: ${ev.new_status}`}
            </div>
            {ev.remarks && <div style={{ marginTop: '0.1rem', color: '#475569' }}>Note: {ev.remarks}</div>}
          </div>
        ))}
      </div>
    </div>
  )
}
