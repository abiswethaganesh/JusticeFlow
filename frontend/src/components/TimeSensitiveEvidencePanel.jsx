import React, { useState } from 'react'
import EvidenceUrgencyBadge from './EvidenceUrgencyBadge'
import PreservationRequestModal from './PreservationRequestModal'
import EvidenceTimeline from './EvidenceTimeline'
import { getEvidenceFileUrl } from '../services/api'


const STATUS_LABELS = {
  NOT_REVIEWED: 'Not Reviewed',
  REVIEW_REQUIRED: 'Review Required',
  PRESERVATION_RECOMMENDED: 'Preservation Recommended',
  PRESERVATION_REQUESTED: 'Request Dispatched',
  PRESERVED: 'Evidence Secured / Preserved',
  NOT_APPLICABLE: 'Exempt / Not Applicable',
  UNKNOWN: 'Unknown Status',
}

const STATUS_COLORS = {
  NOT_REVIEWED: { bg: '#f1f5f9', color: '#475569' },
  REVIEW_REQUIRED: { bg: '#fef3c7', color: '#92400e' },
  PRESERVATION_RECOMMENDED: { bg: '#ffedd5', color: '#9a3412' },
  PRESERVATION_REQUESTED: { bg: '#dbeafe', color: '#1e40af' },
  PRESERVED: { bg: '#dcfce7', color: '#166534' },
  NOT_APPLICABLE: { bg: '#f3f4f6', color: '#6b7280' },
  UNKNOWN: { bg: '#f8fafc', color: '#64748b' },
}

export default function TimeSensitiveEvidencePanel({ evidenceList, onEvidenceUpdated, caseId }) {
  const [selectedEvidence, setSelectedEvidence] = useState(null)
  const [expandedTimelineId, setExpandedTimelineId] = useState(null)

  if (!evidenceList || evidenceList.length === 0) {
    return (
      <div
        style={{
          padding: '1rem',
          background: '#f8fafc',
          borderRadius: '8px',
          border: '1px solid var(--color-border)',
          color: 'var(--color-text-muted)',
          fontSize: '0.85rem',
        }}
      >
        No time-sensitive digital/physical evidence currently flagged for this case.
      </div>
    )
  }

  return (
    <div style={{ marginBottom: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.6rem' }}>
        <div>
          <span className="eyebrow">Time-Aware Evidence Preservation System</span>
          <h3 style={{ fontSize: '1.05rem', margin: 0 }}>⏱️ Early Action & Retention Alerts</h3>
        </div>
        <span
          style={{
            background: '#e0e7ff',
            color: '#3730a3',
            fontSize: '0.75rem',
            fontWeight: 700,
            padding: '0.2rem 0.6rem',
            borderRadius: '12px',
          }}
        >
          {evidenceList.length} Item(s)
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {evidenceList.map((ev) => {
          const stCfg = STATUS_COLORS[ev.preservation_status] || STATUS_COLORS.UNKNOWN
          const isTimelineOpen = expandedTimelineId === ev.id

          return (
            <div
              key={ev.id}
              style={{
                background: '#ffffff',
                border: ev.urgency === 'CRITICAL' || ev.urgency === 'HIGH' ? '1px solid #fcd34d' : '1px solid var(--color-border)',
                borderRadius: '8px',
                padding: '0.85rem 1rem',
                boxShadow: ev.urgency === 'CRITICAL' ? '0 2px 8px rgba(220, 38, 38, 0.08)' : 'none',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.5rem' }}>
                <div>
                  <h4 style={{ fontSize: '0.95rem', margin: 0, fontWeight: 700 }}>
                    {ev.title} <span style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 500 }}>({ev.evidence_type})</span>
                  </h4>
                  {ev.description && (
                    <p style={{ fontSize: '0.83rem', color: '#475569', margin: '0.2rem 0 0.4rem', lineHeight: 1.4 }}>
                      {ev.description}
                    </p>
                  )}
                  <div style={{ fontSize: '0.78rem', color: '#64748b' }}>
                    Source: <strong>{ev.source || 'Extracted from complaint'}</strong>
                    {ev.retention_source && (
                      <span style={{ marginLeft: '0.5rem' }}>
                        • Policy: <em>{ev.retention_source}</em>
                      </span>
                    )}
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.35rem' }}>
                  <EvidenceUrgencyBadge urgency={ev.urgency} confidence={ev.retention_confidence} />
                  <span
                    style={{
                      background: stCfg.bg,
                      color: stCfg.color,
                      fontSize: '0.72rem',
                      fontWeight: 700,
                      padding: '0.15rem 0.45rem',
                      borderRadius: '4px',
                    }}
                  >
                    Status: {STATUS_LABELS[ev.preservation_status] || ev.preservation_status}
                  </span>
                </div>
              </div>

              {/* Action Toolbar */}
              <div
                style={{
                  display: 'flex',
                  justify: 'space-between',
                  alignItems: 'center',
                  marginTop: '0.75rem',
                  paddingTop: '0.6rem',
                  borderTop: '1px solid #f1f5f9',
                }}
              >
                <button
                  className="btn btn-ghost"
                  style={{ fontSize: '0.78rem', padding: '0.2rem 0.4rem', color: '#4f46e5' }}
                  onClick={() => setExpandedTimelineId(isTimelineOpen ? null : ev.id)}
                >
                  {isTimelineOpen ? '▲ Hide Audit Trail' : '▼ Inspect Audit Trail & Metrics'}
                </button>

                <div style={{ display: 'flex', gap: '0.4rem' }}>
                  {ev.file_url && (
                    <>
                      <a
                        href={getEvidenceFileUrl(ev)}
                        target="_blank"
                        rel="noreferrer"
                        className="btn btn-ghost"
                        style={{ fontSize: '0.78rem', padding: '0.25rem 0.55rem' }}
                      >
                        View File ↗
                      </a>
                      <a
                        href={getEvidenceFileUrl(ev, true)}
                        download
                        className="btn btn-ghost"
                        style={{ fontSize: '0.78rem', padding: '0.25rem 0.55rem', color: '#475569' }}
                      >
                        📥 Download
                      </a>
                    </>
                  )}

                  <button
                    className="btn btn-primary"
                    style={{ fontSize: '0.78rem', padding: '0.25rem 0.65rem' }}
                    onClick={() => setSelectedEvidence(ev)}
                  >
                    Review Preservation Request Draft ↗
                  </button>
                </div>
              </div>

              {/* Expanded Audit Trail */}
              {isTimelineOpen && (
                <div style={{ marginTop: '0.6rem', paddingTop: '0.5rem', borderTop: '1px dashed #cbd5e1' }}>
                  <span className="eyebrow" style={{ fontSize: '0.68rem' }}>Audit Trail History</span>
                  <EvidenceTimeline evidenceId={ev.id} />
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Modal Requisition Viewer */}
      {selectedEvidence && (
        <PreservationRequestModal
          evidence={selectedEvidence}
          onClose={() => setSelectedEvidence(null)}
          onActionComplete={(updatedEv) => {
            if (onEvidenceUpdated) onEvidenceUpdated(updatedEv)
          }}
        />
      )}
    </div>
  )
}
