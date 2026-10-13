import React, { useEffect, useState } from 'react'
import { fetchPreservationDraftApi, recordPreservationActionApi, getErrorMessage } from '../services/api'
import EvidenceUrgencyBadge from './EvidenceUrgencyBadge'

export default function PreservationRequestModal({ evidence, onClose, onActionComplete }) {
  const [draft, setDraft] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [acting, setActing] = useState(false)
  const [recipient, setRecipient] = useState('')
  const [narrative, setNarrative] = useState('')
  const [remarks, setRemarks] = useState('')

  useEffect(() => {
    async function loadDraft() {
      if (!evidence) return
      setLoading(true)
      setError(null)
      try {
        const data = await fetchPreservationDraftApi(evidence.id)
        setDraft(data)
        setRecipient(data.target_recipient || '')
        setNarrative(data.requisition_narrative || '')
      } catch (err) {
        setError(getErrorMessage(err, 'Failed to generate preservation request draft.'))
      } finally {
        setLoading(false)
      }
    }
    loadDraft()
  }, [evidence])

  if (!evidence) return null

  const handleAction = async (actionType, statusType) => {
    setActing(true)
    setError(null)
    try {
      const fullRemarks = `[Officer Action: ${actionType}] Recipient: ${recipient}. ${remarks ? 'Notes: ' + remarks : ''}`
      const updated = await recordPreservationActionApi(evidence.id, actionType, statusType, fullRemarks)
      if (onActionComplete) onActionComplete(updated)
      onClose()
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to record preservation action.'))
    } finally {
      setActing(false)
    }
  }

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.65)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 999,
        padding: '1rem',
      }}
    >
      <div
        className="card"
        style={{
          maxWidth: '750px',
          width: '100%',
          maxHeight: '90vh',
          overflowY: 'auto',
          padding: '1.5rem',
          background: '#ffffff',
          borderRadius: '12px',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.2)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
          <div>
            <span className="eyebrow">Officer Reviewable Draft</span>
            <h2 style={{ fontSize: '1.25rem', marginTop: '0.2rem' }}>
              Preservation Requisition — {evidence.title}
            </h2>
            <div style={{ marginTop: '0.35rem' }}>
              <EvidenceUrgencyBadge urgency={evidence.urgency} confidence={evidence.retention_confidence} />
            </div>
          </div>
          <button className="btn btn-ghost" onClick={onClose} style={{ fontSize: '1.2rem', padding: '0.2rem 0.5rem' }}>
            ✕
          </button>
        </div>

        {/* Safety Disclaimer Banner */}
        <div
          style={{
            background: '#eff6ff',
            border: '1px solid #bfdbfe',
            color: '#1e40af',
            padding: '0.75rem',
            borderRadius: '6px',
            fontSize: '0.82rem',
            marginBottom: '1.25rem',
            lineHeight: 1.4,
          }}
        >
          <strong>⚠️ Human-in-the-Loop Safety Notice:</strong> This document is strictly an officer-reviewable DRAFT prepared by JusticeFlow AI.
          The AI system does <em>not</em> automatically issue legal notices or contact external organizations. You must review, edit if needed, and explicitly authorize the requisition.
        </div>

        {loading ? (
          <p style={{ color: 'var(--color-text-muted)', padding: '1rem 0' }}>Generating preservation request draft…</p>
        ) : error ? (
          <div className="error-banner" style={{ marginBottom: '1rem' }}>{error}</div>
        ) : (
          <div>
            {/* Draft Details Form */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', marginBottom: '1.25rem' }}>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 700, color: '#475569', display: 'block', marginBottom: '0.25rem' }}>
                  Requisition Subject Line
                </label>
                <input
                  type="text"
                  readOnly
                  value={draft?.subject || ''}
                  style={{ width: '100%', padding: '0.45rem 0.65rem', fontSize: '0.88rem', background: '#f8fafc', border: '1px solid var(--color-border)', borderRadius: '6px' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 700, color: '#475569', display: 'block', marginBottom: '0.25rem' }}>
                    Target Recipient / Holding Authority
                  </label>
                  <input
                    type="text"
                    value={recipient}
                    onChange={(e) => setRecipient(e.target.value)}
                    placeholder="e.g. Nodal Officer / Shop In-Charge"
                    style={{ width: '100%', padding: '0.45rem 0.65rem', fontSize: '0.88rem', border: '1px solid var(--color-border)', borderRadius: '6px' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 700, color: '#475569', display: 'block', marginBottom: '0.25rem' }}>
                    Retention Source Policy
                  </label>
                  <input
                    type="text"
                    readOnly
                    value={evidence.retention_source || 'Unknown Policy'}
                    style={{ width: '100%', padding: '0.45rem 0.65rem', fontSize: '0.85rem', background: '#f8fafc', border: '1px solid var(--color-border)', borderRadius: '6px' }}
                  />
                </div>
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 700, color: '#475569', display: 'block', marginBottom: '0.25rem' }}>
                  Requisition Statement Narrative
                </label>
                <textarea
                  rows={6}
                  value={narrative}
                  onChange={(e) => setNarrative(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.65rem',
                    fontSize: '0.85rem',
                    fontFamily: 'monospace',
                    lineHeight: 1.45,
                    border: '1px solid var(--color-border)',
                    borderRadius: '6px',
                  }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 700, color: '#475569', display: 'block', marginBottom: '0.25rem' }}>
                  Official Remarks / Dispatch Reference (Optional)
                </label>
                <input
                  type="text"
                  value={remarks}
                  onChange={(e) => setRemarks(e.target.value)}
                  placeholder="e.g. Dispatched via email/hand delivery by SI Suresh..."
                  style={{ width: '100%', padding: '0.45rem 0.65rem', fontSize: '0.85rem', border: '1px solid var(--color-border)', borderRadius: '6px' }}
                />
              </div>
            </div>

            {/* Officer Decision Buttons */}
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', justifyContent: 'flex-end', paddingTop: '0.75rem', borderTop: '1px solid var(--color-border)' }}>
              <button
                className="btn btn-ghost"
                onClick={onClose}
                disabled={acting}
                style={{ fontSize: '0.85rem' }}
              >
                Cancel
              </button>

              <button
                className="btn"
                style={{ background: '#f59e0b', color: 'white', border: 'none', fontSize: '0.85rem' }}
                onClick={() => handleAction('NOT_APPLICABLE_EXEMPT', 'NOT_APPLICABLE')}
                disabled={acting}
              >
                Mark Not Applicable
              </button>

              <button
                className="btn"
                style={{ background: '#2563eb', color: 'white', border: 'none', fontSize: '0.85rem' }}
                onClick={() => handleAction('PRESERVATION_REQUEST_SENT', 'PRESERVATION_REQUESTED')}
                disabled={acting}
              >
                ✓ Mark Request Sent
              </button>

              <button
                className="btn"
                style={{ background: '#16a34a', color: 'white', border: 'none', fontSize: '0.85rem' }}
                onClick={() => handleAction('EVIDENCE_SECURED_PRESERVED', 'PRESERVED')}
                disabled={acting}
              >
                ✓ Mark Evidence Preserved
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
