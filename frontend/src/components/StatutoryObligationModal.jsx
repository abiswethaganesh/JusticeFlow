import React, { useState, useEffect } from 'react'
import {
  fetchObligationAuditTrailApi,
  completeObligationApi,
  markObligationNotApplicableApi,
  requestObligationReviewApi,
  getErrorMessage,
} from '../services/api'
import { StatusBadge } from './StatutoryObligationPanel'

export default function StatutoryObligationModal({ obligation, onClose, onRefresh }) {
  const [activeTab, setActiveTab] = useState('DETAILS') // 'DETAILS' | 'ACTION' | 'AUDIT'
  const [actionType, setActionType] = useState('COMPLETE') // 'COMPLETE' | 'NOT_APPLICABLE' | 'REVIEW'
  const [notes, setNotes] = useState('')
  const [reason, setReason] = useState('')
  const [auditEvents, setAuditEvents] = useState([])
  const [isLoadingAudit, setIsLoadingAudit] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [showConfirmation, setShowConfirmation] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')
  const [successMsg, setSuccessMsg] = useState('')

  useEffect(() => {
    if (obligation?.id) {
      loadAuditEvents()
    }
  }, [obligation?.id])

  async function loadAuditEvents() {
    setIsLoadingAudit(true)
    try {
      const events = await fetchObligationAuditTrailApi(obligation.id)
      setAuditEvents(events || [])
    } catch (e) {
      console.error('Failed to load obligation audit events:', e)
    } finally {
      setIsLoadingAudit(false)
    }
  }

  function handleActionSubmitInitiate(e) {
    e.preventDefault()
    setErrorMsg('')
    setSuccessMsg('')

    if (actionType === 'NOT_APPLICABLE' && !reason.trim()) {
      setErrorMsg('Justification reason is required when marking an obligation as Not Applicable.')
      return
    }

    if (actionType === 'REVIEW' && !reason.trim()) {
      setErrorMsg('Review reason is required when requesting legal or supervisory review.')
      return
    }

    setShowConfirmation(true)
  }

  async function handleConfirmSubmit() {
    setIsSubmitting(true)
    setErrorMsg('')
    setSuccessMsg('')
    setShowConfirmation(false)

    try {
      if (actionType === 'COMPLETE') {
        await completeObligationApi(obligation.id, notes)
        setSuccessMsg('Obligation marked as COMPLETED successfully.')
      } else if (actionType === 'NOT_APPLICABLE') {
        await markObligationNotApplicableApi(obligation.id, reason)
        setSuccessMsg('Obligation marked as NOT APPLICABLE.')
      } else if (actionType === 'REVIEW') {
        await requestObligationReviewApi(obligation.id, reason)
        setSuccessMsg('Legal / procedural review request registered successfully.')
      }

      await loadAuditEvents()
      if (onRefresh) onRefresh()
    } catch (err) {
      setErrorMsg(getErrorMessage(err, 'Failed to update obligation state.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!obligation) return null

  const isQualitative = obligation.rule?.deadline_unit === 'QUALITATIVE' || !obligation.due_date

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        background: 'rgba(15, 23, 42, 0.65)',
        backdropFilter: 'blur(4px)',
        WebkitBackdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1.25rem',
        overflowY: 'auto',
      }}
    >
      <div
        style={{
          background: '#FFFFFF',
          borderRadius: '16px',
          boxShadow: '0 25px 50px -12px rgba(15, 42, 74, 0.35)',
          border: '1px solid #CBD7E6',
          width: '100%',
          maxWidth: '680px',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          animation: 'fadeInModal 0.2s ease-out',
        }}
      >
        {/* Modal Header in Navy Blue #0F2A4A */}
        <div
          style={{
            background: '#0F2A4A',
            color: '#FFFFFF',
            padding: '1.25rem 1.5rem',
            borderBottom: '1px solid #17395E',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                <span
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.72rem',
                    fontWeight: 700,
                    background: '#17395E',
                    color: '#EBF3FA',
                    padding: '0.15rem 0.5rem',
                    borderRadius: '4px',
                    border: '1px solid #245789',
                  }}
                >
                  {obligation.case_id}
                </span>
                <StatusBadge status={obligation.status} escalationStatus={obligation.escalation_status} />
              </div>

              <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#FFFFFF', marginTop: '0.5rem', lineHeight: '1.3' }}>
                {obligation.rule?.title || 'Statutory Obligation'}
              </h2>

              <div style={{ fontSize: '0.78rem', color: '#9FB3C8', fontFamily: 'var(--font-mono)', fontWeight: 500, marginTop: '0.2rem' }}>
                {obligation.rule?.legal_source} — Section {obligation.rule?.section_reference}
              </div>
            </div>

            <button
              type="button"
              onClick={onClose}
              aria-label="Close modal"
              style={{
                background: 'transparent',
                border: 'none',
                color: '#9FB3C8',
                fontSize: '1.4rem',
                lineHeight: 1,
                cursor: 'pointer',
                padding: '0.2rem 0.4rem',
                borderRadius: '4px',
                transition: 'color 0.15s ease',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = '#FFFFFF')}
              onMouseLeave={(e) => (e.currentTarget.style.color = '#9FB3C8')}
            >
              &times;
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div
          style={{
            display: 'flex',
            background: '#F4F7FA',
            borderBottom: '1px solid #E1E5EB',
            padding: '0 1rem',
          }}
        >
          <button
            type="button"
            onClick={() => setActiveTab('DETAILS')}
            style={{
              padding: '0.85rem 1rem',
              fontSize: '0.8rem',
              fontWeight: activeTab === 'DETAILS' ? 700 : 600,
              color: activeTab === 'DETAILS' ? '#0F2A4A' : '#5C6773',
              background: 'transparent',
              border: 'none',
              borderBottom: activeTab === 'DETAILS' ? '3px solid #0F2A4A' : '3px solid transparent',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
          >
            Overview &amp; Details
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('ACTION')}
            style={{
              padding: '0.85rem 1rem',
              fontSize: '0.8rem',
              fontWeight: activeTab === 'ACTION' ? 700 : 600,
              color: activeTab === 'ACTION' ? '#0F2A4A' : '#5C6773',
              background: 'transparent',
              border: 'none',
              borderBottom: activeTab === 'ACTION' ? '3px solid #0F2A4A' : '3px solid transparent',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
          >
            Officer Actions
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('AUDIT')}
            style={{
              padding: '0.85rem 1rem',
              fontSize: '0.8rem',
              fontWeight: activeTab === 'AUDIT' ? 700 : 600,
              color: activeTab === 'AUDIT' ? '#0F2A4A' : '#5C6773',
              background: 'transparent',
              border: 'none',
              borderBottom: activeTab === 'AUDIT' ? '3px solid #0F2A4A' : '3px solid transparent',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
          >
            Accountability Audit Trail ({auditEvents.length})
          </button>
        </div>

        {/* Modal Body Container */}
        <div style={{ padding: '1.25rem', overflowY: 'auto', flex: 1 }}>
          {errorMsg && (
            <div
              style={{
                padding: '0.75rem 1rem',
                borderRadius: '8px',
                background: '#FCEAEA',
                border: '1px solid #F5C6C6',
                color: '#B3261E',
                fontSize: '0.8rem',
                fontWeight: 600,
                marginBottom: '1rem',
              }}
            >
              {errorMsg}
            </div>
          )}

          {successMsg && (
            <div
              style={{
                padding: '0.75rem 1rem',
                borderRadius: '8px',
                background: '#E7F6EC',
                border: '1px solid #B6E6C5',
                color: '#157F3C',
                fontSize: '0.8rem',
                fontWeight: 600,
                marginBottom: '1rem',
              }}
            >
              ✓ {successMsg}
            </div>
          )}

          {/* TAB 1: OVERVIEW */}
          {activeTab === 'DETAILS' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', fontSize: '0.82rem' }}>
              {/* Applicability Section Card */}
              <div
                style={{
                  background: '#F0F5FA',
                  padding: '1rem',
                  borderRadius: '10px',
                  border: '1px solid #CBD7E6',
                }}
              >
                <div
                  style={{
                    fontWeight: 700,
                    color: '#0F2A4A',
                    fontSize: '0.75rem',
                    textTransform: 'uppercase',
                    letterSpacing: '0.04em',
                    marginBottom: '0.35rem',
                  }}
                >
                  Applicability &amp; Statutory Scope
                </div>
                <p style={{ color: '#243342', lineHeight: '1.5', margin: 0 }}>{obligation.applicability_reason}</p>
                {obligation.review_reason && (
                  <div
                    style={{
                      marginTop: '0.75rem',
                      background: '#F3E8FF',
                      padding: '0.65rem 0.85rem',
                      borderRadius: '6px',
                      border: '1px solid #E9D5FF',
                      color: '#6B21A8',
                      fontSize: '0.8rem',
                    }}
                  >
                    <strong>Review Note:</strong> {obligation.review_reason}
                  </div>
                )}
              </div>

              {/* Deadline Section Card */}
              <div
                style={{
                  background: '#FFFFFF',
                  padding: '1rem',
                  borderRadius: '10px',
                  border: '1px solid #CBD7E6',
                }}
              >
                <div
                  style={{
                    fontWeight: 700,
                    color: '#0F2A4A',
                    fontSize: '0.75rem',
                    textTransform: 'uppercase',
                    letterSpacing: '0.04em',
                    marginBottom: '0.5rem',
                  }}
                >
                  Deadline &amp; Compliance Timeline
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', fontSize: '0.8rem' }}>
                  <div>
                    <span style={{ color: '#5C6773' }}>Start Date: </span>
                    <strong style={{ color: '#0F2A4A' }}>
                      {new Date(obligation.start_date).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })}
                    </strong>
                  </div>
                  <div>
                    <span style={{ color: '#5C6773' }}>Statutory Due Date: </span>
                    {isQualitative ? (
                      <strong style={{ color: '#5C6773', fontStyle: 'italic' }}>No Fixed Numeric Due Date</strong>
                    ) : (
                      <strong style={{ color: obligation.status === 'OVERDUE' ? '#B3261E' : '#0F2A4A' }}>
                        {new Date(obligation.due_date).toLocaleString('en-IN', { dateStyle: 'medium' })}
                      </strong>
                    )}
                  </div>
                </div>
                {isQualitative && (
                  <div style={{ fontSize: '0.75rem', color: '#5C6773', fontStyle: 'italic', marginTop: '0.4rem' }}>
                    Procedural monitoring (periodical investigation progress communication requirement).
                  </div>
                )}
              </div>

              {/* Legal Source Section Card */}
              <div
                style={{
                  background: '#FFFFFF',
                  padding: '1rem',
                  borderRadius: '10px',
                  border: '1px solid #CBD7E6',
                }}
              >
                <div
                  style={{
                    fontWeight: 700,
                    color: '#0F2A4A',
                    fontSize: '0.75rem',
                    textTransform: 'uppercase',
                    letterSpacing: '0.04em',
                    marginBottom: '0.35rem',
                  }}
                >
                  Legal Provision &amp; Mandate
                </div>
                <div style={{ color: '#243342', lineHeight: '1.5' }}>{obligation.rule?.description}</div>
                {obligation.rule?.source_url && (
                  <div style={{ marginTop: '0.75rem' }}>
                    <a
                      href={obligation.rule.source_url}
                      target="_blank"
                      rel="noreferrer"
                      style={{
                        fontSize: '0.78rem',
                        color: '#245789',
                        fontWeight: 600,
                        textDecoration: 'none',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.25rem',
                      }}
                    >
                      Verified Official India Code Source &rsaquo;
                    </a>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: OFFICER ACTIONS */}
          {activeTab === 'ACTION' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', fontSize: '0.82rem' }}>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  type="button"
                  onClick={() => setActionType('COMPLETE')}
                  style={{
                    flex: 1,
                    padding: '0.6rem',
                    borderRadius: '8px',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    border: '1px solid',
                    borderColor: actionType === 'COMPLETE' ? '#157F3C' : '#CBD7E6',
                    background: actionType === 'COMPLETE' ? '#157F3C' : '#FFFFFF',
                    color: actionType === 'COMPLETE' ? '#FFFFFF' : '#243342',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  Complete Obligation
                </button>
                <button
                  type="button"
                  onClick={() => setActionType('NOT_APPLICABLE')}
                  style={{
                    flex: 1,
                    padding: '0.6rem',
                    borderRadius: '8px',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    border: '1px solid',
                    borderColor: actionType === 'NOT_APPLICABLE' ? '#334155' : '#CBD7E6',
                    background: actionType === 'NOT_APPLICABLE' ? '#334155' : '#FFFFFF',
                    color: actionType === 'NOT_APPLICABLE' ? '#FFFFFF' : '#243342',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  Mark Not Applicable
                </button>
                <button
                  type="button"
                  onClick={() => setActionType('REVIEW')}
                  style={{
                    flex: 1,
                    padding: '0.6rem',
                    borderRadius: '8px',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    border: '1px solid',
                    borderColor: actionType === 'REVIEW' ? '#6B21A8' : '#CBD7E6',
                    background: actionType === 'REVIEW' ? '#6B21A8' : '#FFFFFF',
                    color: actionType === 'REVIEW' ? '#FFFFFF' : '#243342',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  Request Review
                </button>
              </div>

              <form onSubmit={handleActionSubmitInitiate} style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {actionType === 'COMPLETE' && (
                  <div>
                    <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#0F2A4A', marginBottom: '0.35rem' }}>
                      Compliance Notes / Investigation Summary
                    </label>
                    <textarea
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      rows={4}
                      placeholder="Enter details of compliance (e.g., Progress report sent to informant on 18 Sep 2026 via electronic communication)."
                      style={{
                        width: '100%',
                        fontSize: '0.82rem',
                        padding: '0.65rem 0.85rem',
                        borderRadius: '8px',
                        border: '1px solid #CBD7E6',
                        outline: 'none',
                        boxSizing: 'border-box',
                        fontFamily: 'inherit',
                      }}
                    />
                  </div>
                )}

                {actionType === 'NOT_APPLICABLE' && (
                  <div>
                    <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#0F2A4A', marginBottom: '0.35rem' }}>
                      Justification Reason for Non-Applicability <span style={{ color: '#B3261E' }}>*</span>
                    </label>
                    <textarea
                      value={reason}
                      onChange={(e) => setReason(e.target.value)}
                      rows={4}
                      placeholder="Specify why this statutory obligation does not apply to this case."
                      style={{
                        width: '100%',
                        fontSize: '0.82rem',
                        padding: '0.65rem 0.85rem',
                        borderRadius: '8px',
                        border: '1px solid #CBD7E6',
                        outline: 'none',
                        boxSizing: 'border-box',
                        fontFamily: 'inherit',
                      }}
                      required
                    />
                  </div>
                )}

                {actionType === 'REVIEW' && (
                  <div>
                    <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#0F2A4A', marginBottom: '0.35rem' }}>
                      Reason for Legal / Procedural Review Request <span style={{ color: '#B3261E' }}>*</span>
                    </label>
                    <textarea
                      value={reason}
                      onChange={(e) => setReason(e.target.value)}
                      rows={4}
                      placeholder="Describe legal or factual ambiguity requiring supervisory or legal review."
                      style={{
                        width: '100%',
                        fontSize: '0.82rem',
                        padding: '0.65rem 0.85rem',
                        borderRadius: '8px',
                        border: '1px solid #CBD7E6',
                        outline: 'none',
                        boxSizing: 'border-box',
                        fontFamily: 'inherit',
                      }}
                      required
                    />
                  </div>
                )}

                {showConfirmation && (
                  <div
                    style={{
                      padding: '0.85rem 1rem',
                      borderRadius: '8px',
                      background: '#FDF1DD',
                      border: '1px solid #F8D8A8',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.5rem',
                    }}
                  >
                    <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#A15C00' }}>
                      Confirm Action: Update obligation state to{' '}
                      <strong>
                        {actionType === 'COMPLETE' ? 'Completed' : actionType === 'NOT_APPLICABLE' ? 'Not Applicable' : 'Request Review'}
                      </strong>?
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                      <button
                        type="button"
                        onClick={() => setShowConfirmation(false)}
                        style={{
                          padding: '0.35rem 0.75rem',
                          fontSize: '0.78rem',
                          fontWeight: 600,
                          color: '#243342',
                          background: '#FFFFFF',
                          border: '1px solid #CBD7E6',
                          borderRadius: '6px',
                          cursor: 'pointer',
                        }}
                      >
                        Cancel
                      </button>
                      <button
                        type="button"
                        onClick={handleConfirmSubmit}
                        disabled={isSubmitting}
                        style={{
                          padding: '0.35rem 0.85rem',
                          fontSize: '0.78rem',
                          fontWeight: 700,
                          color: '#FFFFFF',
                          background: '#0F2A4A',
                          border: 'none',
                          borderRadius: '6px',
                          cursor: 'pointer',
                        }}
                      >
                        {isSubmitting ? 'Updating...' : 'Confirm Action'}
                      </button>
                    </div>
                  </div>
                )}

                {!showConfirmation && (
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    style={{
                      width: '100%',
                      padding: '0.65rem',
                      borderRadius: '8px',
                      fontSize: '0.82rem',
                      fontWeight: 700,
                      color: '#FFFFFF',
                      background: '#0F2A4A',
                      border: 'none',
                      cursor: 'pointer',
                      boxShadow: '0 2px 4px rgba(15, 42, 74, 0.15)',
                    }}
                  >
                    Save &amp; Record Action
                  </button>
                )}
              </form>
            </div>
          )}

          {/* TAB 3: AUDIT TRAIL */}
          {activeTab === 'AUDIT' && (
            <div>
              {isLoadingAudit ? (
                <div style={{ padding: '1.5rem', textAlign: 'center', color: '#5C6773', fontSize: '0.82rem' }}>
                  Loading audit trail...
                </div>
              ) : auditEvents.length === 0 ? (
                <div style={{ padding: '1.5rem', textAlign: 'center', color: '#5C6773', fontSize: '0.82rem' }}>
                  No audit events recorded yet.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', paddingLeft: '0.5rem' }}>
                  {auditEvents.map((evt) => (
                    <div
                      key={evt.id}
                      style={{
                        background: '#F0F5FA',
                        padding: '0.75rem 1rem',
                        borderRadius: '8px',
                        border: '1px solid #CBD7E6',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.8rem' }}>
                        <span style={{ fontWeight: 700, color: '#0F2A4A' }}>{evt.action.replace(/_/g, ' ')}</span>
                        <span style={{ fontSize: '0.75rem', color: '#5C6773', fontFamily: 'var(--font-mono)' }}>
                          {new Date(evt.timestamp).toLocaleString('en-IN', { dateStyle: 'short', timeStyle: 'short' })}
                        </span>
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#395778', marginTop: '0.2rem' }}>
                        Actor: <strong>{evt.actor_name}</strong> ({evt.actor_role})
                      </div>
                      {evt.remarks && (
                        <div
                          style={{
                            fontSize: '0.78rem',
                            color: '#243342',
                            fontStyle: 'italic',
                            marginTop: '0.35rem',
                            background: '#FFFFFF',
                            padding: '0.5rem',
                            borderRadius: '4px',
                            border: '1px solid #E1E5EB',
                          }}
                        >
                          "{evt.remarks}"
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div
          style={{
            background: '#F4F7FA',
            padding: '0.85rem 1.25rem',
            borderTop: '1px solid #E1E5EB',
            display: 'flex',
            justifyContent: 'flex-end',
          }}
        >
          <button
            type="button"
            onClick={onClose}
            style={{
              padding: '0.45rem 1rem',
              background: '#FFFFFF',
              border: '1px solid #CBD7E6',
              color: '#0F2A4A',
              fontSize: '0.8rem',
              fontWeight: 600,
              borderRadius: '6px',
              cursor: 'pointer',
            }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

