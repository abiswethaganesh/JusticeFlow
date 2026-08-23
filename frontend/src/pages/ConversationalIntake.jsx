import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { analyzeIntakeApi, createComplaintApi, getErrorMessage } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { useComplaintWorkflow } from '../context/ComplaintWorkflowContext'
import EvidenceUploader from '../components/EvidenceUploader'
import ProgressSteps from '../components/ProgressSteps'
import DynamicComplaintForm from '../components/DynamicComplaintForm'
import { FORM_SCHEMAS, getMissingFields } from '../data/formSchemas'

const PROCESSING_STEPS = [
  'Analyzing complaint input',
  'Identifying complaint classification',
  'Extracting incident information',
  'Checking missing & ambiguous details',
  'Formulating intake response',
]

export default function ConversationalIntake() {
  const { user } = useAuth()
  const { workflow, updateWorkflow, resetWorkflow } = useComplaintWorkflow()
  const navigate = useNavigate()
  const messagesEndRef = useRef(null)

  const [inputMessage, setInputMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [processingStep, setProcessingStep] = useState(1)
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [submittedRecord, setSubmittedRecord] = useState(null)
  const [showReviewModal, setShowReviewModal] = useState(false)

  // Current analysis state
  const analysis = workflow.analysis
  const messages = workflow.messages || []
  const uploadedFiles = workflow.evidenceFiles || []
  const manualAnswers = workflow.manualAnswers || {}

  // Reset workflow if previous completed case exists when entering intake
  useEffect(() => {
    if (workflow.lastCaseId) {
      resetWorkflow()
    }
  }, [])

  const mergedEntities = { ...(analysis?.entities || {}), ...manualAnswers }
  const currentComplaintType = analysis?.complaint_type || 'other'
  const schema = FORM_SCHEMAS[currentComplaintType] || FORM_SCHEMAS.other
  const missingFields = analysis ? getMissingFields(currentComplaintType, mergedEntities) : []

  const handleEntityChange = (fieldKey, value) => {
    const updatedManual = { ...manualAnswers, [fieldKey]: value }
    updateWorkflow({
      manualAnswers: updatedManual,
    })
  }

  const handleSendMessage = async (textToSend) => {
    const query = textToSend || inputMessage
    if (!query || !query.trim() || loading) return

    const newMsg = {
      id: Date.now(),
      sender: 'user',
      text: query.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }

    const isFirstMessage = messages.length === 0
    const updatedHistory = [...messages, newMsg]
    const historyToSend = isFirstMessage ? [newMsg] : updatedHistory
    const previousEntitiesToSend = isFirstMessage ? {} : mergedEntities

    setInputMessage('')
    setLoading(true)
    setProcessingStep(1)
    setError(null)

    // Dynamic processing step timer
    const stepInterval = setInterval(() => {
      setProcessingStep((prev) => (prev < 5 ? prev + 1 : prev))
    }, 350)

    try {
      const res = await analyzeIntakeApi({
        complaint_text: query.trim(),
        conversation_history: historyToSend,
        previous_entities: previousEntitiesToSend,
      })

      clearInterval(stepInterval)
      setProcessingStep(5)

      const aiFollowUp = res.follow_up_questions?.[0]
      let aiText = res.summary || 'I have analyzed your input and extracted incident details.'
      if (aiFollowUp) {
        aiText += `\n\n"${aiFollowUp}"`
      } else if (res.missing_fields && res.missing_fields.length === 0) {
        aiText += '\n\nInformation collected. All required incident details are complete.'
      }

      const aiMsg = {
        id: Date.now() + 1,
        sender: 'ai',
        text: aiText,
        analysisData: res,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }

      updateWorkflow({
        complaintText: workflow.complaintText ? `${workflow.complaintText}\n${query.trim()}` : query.trim(),
        messages: [...updatedHistory, aiMsg],
        analysis: res,
      })
    } catch (err) {
      clearInterval(stepInterval)
      setError(getErrorMessage(err, 'Failed to process complaint input with Conversational AI.'))
    } finally {
      setLoading(false)
    }
  }

  const handleEvidenceUploaded = (evidenceItem) => {
    updateWorkflow({
      evidenceFiles: [...uploadedFiles, evidenceItem],
    })
  }

  const handleFinalSubmit = async () => {
    setSubmitting(true)
    setError(null)
    try {
      const record = await createComplaintApi({
        complaint_type: currentComplaintType,
        complaint_text: workflow.complaintText,
        summary: analysis?.summary || '',
        structured_data: mergedEntities,
        citizen_phone: user?.phone || mergedEntities.complainant_phone || '',
        citizen_id: user?.id || null,
        incident_details: {
          location: mergedEntities.incident_location || mergedEntities.snatching_location || mergedEntities.office_location || mergedEntities.property_location || '',
          date: mergedEntities.incident_date || mergedEntities.last_seen_date || '',
          time: mergedEntities.incident_time || '',
        },
        is_cognizable: analysis?.is_cognizable ?? true,
        priority: 'MEDIUM',
      })

      updateWorkflow({ lastCaseId: record.case_id })
      setSubmittedRecord(record)
      setShowReviewModal(false)
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to register official case.'))
    } finally {
      setSubmitting(false)
    }
  }

  if (submittedRecord) {
    return (
      <div className="card card-pad success-panel" style={{ textAlign: 'center', marginTop: '2rem' }}>
        <div className="success-icon">✓</div>
        <h2>Official Case Registered in System</h2>
        <div className="success-case-id">{submittedRecord.case_id}</div>

        <div
          style={{
            background: 'white',
            padding: '1rem',
            borderRadius: '8px',
            border: '1px solid var(--color-border)',
            margin: '1.25rem auto',
            maxWidth: '440px',
            textAlign: 'left',
          }}
        >
          <div style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)' }}>Assigned Jurisdiction Station:</div>
          <div style={{ fontSize: '1.05rem', color: 'var(--color-primary)', fontWeight: 700, marginTop: '0.2rem' }}>
            {submittedRecord.assigned_station}
          </div>
          <div style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)', marginTop: '0.75rem' }}>
            Complaint Classification:
          </div>
          <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>
            {submittedRecord.complaint_type.replace('_', ' ').toUpperCase()} ({submittedRecord.is_cognizable ? 'Cognizable' : 'Non-Cognizable'})
          </div>
        </div>

        <div className="btn-row" style={{ justifyContent: 'center' }}>
          <button className="btn btn-primary" onClick={() => navigate(`/status/${submittedRecord.case_id}`)}>
            Track Case Status
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => {
              resetWorkflow()
              navigate('/')
            }}
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    )
  }

  const activeFollowUp = analysis?.follow_up_questions?.[0]
  const currentStepKey = activeFollowUp ? 'complete' : analysis ? 'submit' : 'register'
  const latestAiIndex = messages.findLastIndex((m) => m.sender === 'ai')

  return (
    <>
      <ProgressSteps currentStep={currentStepKey} />

      <div className="page-header">
        <h1>FIR-Aware Conversational Complaint Intake</h1>
        <p>Describe your incident in natural language. JusticeFlow AI determines required CCTNS fields, asks missing details one by one, populates your specific FIR form, and lets you review before registration.</p>
      </div>

      <div className="intake-grid" style={{ display: 'grid', gridTemplateColumns: 'minmax(320px, 1fr) minmax(360px, 460px)', gap: '1.25rem' }}>
        {/* Primary Left Column: Conversational Chat Thread */}
        <div>
          <div className="card" style={{ display: 'flex', flexDirection: 'column', minHeight: '620px' }}>
            <div className="card-pad" style={{ borderBottom: '1px solid var(--color-border)', paddingBottom: '0.75rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2 style={{ fontSize: '1.05rem', margin: 0 }}>Conversational Intake Assistant</h2>
              <span style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', background: '#f1f5f9', padding: '0.2rem 0.5rem', borderRadius: '4px' }}>
                State Police CCTNS Engine
              </span>
            </div>

            {/* Scrollable Chat Area */}
            <div style={{ flex: 1, padding: '1.25rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {/* Initial Statement Input Box when no messages exist yet */}
              {messages.length === 0 && (
                <div style={{ background: '#ffffff', border: '1px solid var(--color-border)', borderRadius: '12px', padding: '1.5rem', boxShadow: '0 2px 8px rgba(0,0,0,0.04)' }}>
                  <div style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--color-text-main)', marginBottom: '0.4rem' }}>
                    Describe your complaint incident
                  </div>
                  <p style={{ fontSize: '0.88rem', color: 'var(--color-text-muted)', marginBottom: '1rem' }}>
                    Describe what happened in your own words (e.g. "My phone was snatched in Anna Nagar yesterday", "My motorcycle was stolen", or "I was cheated in an online fraud").
                  </p>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    <textarea
                      rows={3}
                      placeholder="Type your complaint statement here..."
                      value={inputMessage}
                      onChange={(e) => setInputMessage(e.target.value)}
                      disabled={loading}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault()
                          handleSendMessage()
                        }
                      }}
                      style={{ width: '100%', padding: '0.75rem', fontSize: '0.92rem', borderRadius: '8px', border: '1px solid var(--color-border-strong)' }}
                    />
                    <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                      <button
                        className="btn btn-primary"
                        onClick={() => handleSendMessage()}
                        disabled={loading || !inputMessage.trim()}
                        style={{ padding: '0.65rem 1.4rem' }}
                      >
                        {loading ? 'Processing Statement…' : 'Submit Complaint Statement'}
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Chat Messages */}
              {messages.map((msg, idx) => {
                const isLatestAi = idx === latestAiIndex && !loading
                const questionToAnswer = isLatestAi ? msg.analysisData?.follow_up_questions?.[0] : null

                return (
                  <div
                    key={msg.id}
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                    }}
                  >
                    <div style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', marginBottom: '0.2rem', paddingInline: '0.2rem' }}>
                      {msg.sender === 'user' ? user?.full_name || 'Citizen' : 'JusticeFlow AI'}
                    </div>

                    <div
                      style={{
                        maxWidth: '88%',
                        padding: '0.9rem 1.15rem',
                        borderRadius: msg.sender === 'user' ? '14px 14px 2px 14px' : '14px 14px 14px 2px',
                        background: msg.sender === 'user' ? 'var(--color-blue-accent, #2E6FD9)' : '#f1f5f9',
                        color: msg.sender === 'user' ? 'white' : 'var(--color-text-main, #0f172a)',
                        fontSize: '0.92rem',
                        lineHeight: 1.5,
                        boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                        whiteSpace: 'pre-wrap',
                      }}
                    >
                      <div>{msg.text}</div>

                      {/* AI Analysis Classification Badges */}
                      {msg.sender === 'ai' && msg.analysisData && (
                        <div style={{ marginTop: '0.75rem', borderTop: '1px solid var(--color-border)', paddingTop: '0.6rem' }}>
                          <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
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
                              CLASSIFICATION: {msg.analysisData.complaint_type.replace('_', ' ').toUpperCase()}
                            </span>
                            <span
                              style={{
                                background: msg.analysisData.is_cognizable ? '#fef2f2' : '#f0fdf4',
                                color: msg.analysisData.is_cognizable ? '#991b1b' : '#166534',
                                fontSize: '0.75rem',
                                fontWeight: 700,
                                padding: '0.15rem 0.5rem',
                                borderRadius: '4px',
                              }}
                            >
                              {msg.analysisData.is_cognizable ? 'COGNIZABLE OFFENSE' : 'NON-COGNIZABLE'}
                            </span>
                          </div>

                          {(!msg.analysisData.follow_up_questions || msg.analysisData.follow_up_questions.length === 0) &&
                            missingFields.length === 0 && (
                              <div
                                style={{
                                  marginTop: '0.6rem',
                                  padding: '0.5rem 0.75rem',
                                  background: '#f0fdf4',
                                  borderLeft: '3px solid #16a34a',
                                  borderRadius: '4px',
                                  fontSize: '0.85rem',
                                  fontWeight: 600,
                                  color: '#166534',
                                }}
                              >
                                ✓ All CCTNS required fields collected. Ready for draft review.
                              </div>
                            )}
                        </div>
                      )}
                    </div>

                    {/* Clean White Answer Input Box rendered ONLY under the CURRENT active AI Question */}
                    {questionToAnswer && (
                      <div
                        style={{
                          marginTop: '0.6rem',
                          background: '#ffffff',
                          border: '1px solid var(--color-border)',
                          borderRadius: '8px',
                          padding: '0.75rem 1rem',
                          maxWidth: '88%',
                          width: '100%',
                          boxShadow: '0 2px 6px rgba(0,0,0,0.04)',
                        }}
                      >
                        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
                          <input
                            type="text"
                            placeholder="Type your answer here..."
                            value={inputMessage}
                            onChange={(e) => setInputMessage(e.target.value)}
                            disabled={loading}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') {
                                e.preventDefault()
                                handleSendMessage()
                              }
                            }}
                            style={{
                              flex: 1,
                              minWidth: '200px',
                              padding: '0.6rem 0.8rem',
                              fontSize: '0.88rem',
                              borderRadius: '6px',
                              border: '1px solid var(--color-border-strong)',
                              background: 'white',
                            }}
                          />
                          <button
                            className="btn btn-primary"
                            onClick={() => handleSendMessage()}
                            disabled={loading || !inputMessage.trim()}
                            style={{ padding: '0.6rem 1.25rem', fontSize: '0.85rem' }}
                          >
                            {loading ? 'Submitting…' : 'Submit Answer'}
                          </button>
                        </div>
                      </div>
                    )}

                    <div style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', marginTop: '0.2rem', paddingInline: '0.2rem' }}>
                      {msg.timestamp}
                    </div>
                  </div>
                )
              })}

              {/* Dynamic AI Processing Indicator */}
              {loading && messages.length === 0 && (
                <div
                  style={{
                    background: '#ffffff',
                    border: '1px solid var(--color-border)',
                    borderRadius: '8px',
                    padding: '0.85rem 1rem',
                    maxWidth: '85%',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                  }}
                >
                  <div
                    style={{
                      fontSize: '0.82rem',
                      fontWeight: 700,
                      color: 'var(--color-primary)',
                      marginBottom: '0.5rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                    }}
                  >
                    JusticeFlow AI Engine Processing…
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', fontSize: '0.82rem' }}>
                    {PROCESSING_STEPS.map((stepLabel, idx) => {
                      const isCompleted = processingStep > idx + 1
                      const isCurrent = processingStep === idx + 1
                      return (
                        <div
                          key={idx}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            color: isCompleted ? '#16a34a' : isCurrent ? 'var(--color-primary)' : '#94a3b8',
                            fontWeight: isCurrent ? 600 : 400,
                          }}
                        >
                          <span>{stepLabel}</span>
                          <span style={{ fontWeight: 700, fontSize: '0.85rem' }}>
                            {isCompleted ? '✓' : isCurrent ? '…' : '○'}
                          </span>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {error && <div className="error-banner" style={{ margin: '0.5rem 1rem' }}>{error}</div>}
          </div>
        </div>

        {/* Right Column: Dynamic CCTNS Complaint Form & Registration Action */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {analysis && (
            <DynamicComplaintForm
              complaintType={currentComplaintType}
              entities={mergedEntities}
              missingFields={missingFields}
              isCognizable={analysis.is_cognizable ?? true}
              onEntityChange={handleEntityChange}
            />
          )}

          {analysis && (
            <EvidenceUploader
              caseId={workflow.lastCaseId}
              recommendedEvidence={analysis.recommended_evidence || schema.recommended_evidence || []}
              onEvidenceUploaded={handleEvidenceUploaded}
            />
          )}

          {analysis && (() => {
            const hasMissing = missingFields.length > 0

            return (
              <div
                className="card card-pad"
                style={{
                  background: hasMissing ? '#fffbeb' : '#f0fdf4',
                  border: hasMissing ? '1px solid #fde68a' : '1px solid #86efac',
                  borderRadius: '12px',
                }}
              >
                <span className="eyebrow" style={{ color: hasMissing ? '#b45309' : '#166534', fontWeight: 700 }}>
                  {hasMissing ? 'Missing CCTNS Requirements' : 'Draft Ready for Citizen Confirmation'}
                </span>
                <h3 style={{ fontSize: '1rem', color: hasMissing ? '#92400e' : '#14532d', marginBottom: '0.4rem', fontWeight: 700 }}>
                  {hasMissing ? `${missingFields.length} Mandatory Details Needed` : 'Review & Confirm Complaint Draft'}
                </h3>
                <p style={{ fontSize: '0.82rem', color: hasMissing ? '#78350f' : '#166534', marginBottom: '0.85rem', lineHeight: 1.4 }}>
                  {hasMissing
                    ? `Please answer the AI question in the chat or tap any missing field in the Case Review Panel above to complete your FIR draft.`
                    : 'All required fields for this complaint category have been collected and verified. Click below to inspect your populated FIR draft and register the case.'}
                </p>

                <button
                  className="btn btn-primary"
                  style={{
                    width: '100%',
                    justifyContent: 'center',
                    background: hasMissing ? '#94a3b8' : '#16a34a',
                    borderColor: hasMissing ? '#94a3b8' : '#16a34a',
                    cursor: hasMissing ? 'not-allowed' : 'pointer',
                    fontWeight: 700,
                  }}
                  onClick={() => setShowReviewModal(true)}
                  disabled={hasMissing}
                >
                  {hasMissing ? `Complete ${missingFields.length} Missing Detail(s) First` : '📄 Review & Confirm FIR Draft'}
                </button>
              </div>
            )
          })()}

        </div>
      </div>

      {/* Citizen FIR Draft Review Modal */}
      {showReviewModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(15, 23, 42, 0.65)',
            backdropFilter: 'blur(4px)',
            zIndex: 9999,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '1rem',
          }}
        >
          <div
            className="card card-pad"
            style={{
              maxWidth: '680px',
              width: '100%',
              maxHeight: '90vh',
              overflowY: 'auto',
              background: '#ffffff',
              borderRadius: '12px',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.2)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
              <div>
                <span className="eyebrow" style={{ color: 'var(--color-primary)' }}>Official Citizen Pre-Registration Verification</span>
                <h2 style={{ fontSize: '1.25rem', marginTop: '0.2rem', margin: 0 }}>
                  Review Form IIF-I — {schema.title}
                </h2>
              </div>
              <button
                className="btn btn-ghost"
                onClick={() => setShowReviewModal(false)}
                style={{ fontSize: '1.2rem', padding: '0.2rem 0.5rem', lineHeight: 1 }}
              >
                ✕
              </button>
            </div>

            <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: '1rem' }}>
              Please review all extracted details below. Once confirmed, this case will be registered in PostgreSQL and dispatched to your jurisdiction police station.
            </p>

            <DynamicComplaintForm
              complaintType={currentComplaintType}
              entities={mergedEntities}
              missingFields={[]}
              isCognizable={analysis?.is_cognizable ?? true}
              onEntityChange={handleEntityChange}
              readOnly={false}
            />

            {/* Evidence summary */}
            <div style={{ marginTop: '1rem', background: '#f8fafc', padding: '0.85rem', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
              <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--color-text-main)' }}>
                Attached Evidence Files ({uploadedFiles.length})
              </div>
              {uploadedFiles.length === 0 ? (
                <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.2rem' }}>
                  No evidence files attached yet. (You can still add files after registration).
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem', marginTop: '0.4rem', fontSize: '0.82rem' }}>
                  {uploadedFiles.map((f, i) => (
                    <div key={i} style={{ display: 'flex', justifyContent: 'space-between', color: '#1e293b' }}>
                      <span>📎 {f.title || f.filename}</span>
                      <span style={{ color: '#16a34a', fontWeight: 600 }}>Attached</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Legal recommendations */}
            {analysis?.ai_recommendations?.legal_sections && (
              <div style={{ marginTop: '0.85rem', background: '#eff6ff', border: '1px solid #bfdbfe', padding: '0.75rem', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#1d4ed8' }}>
                  Applicable Legal Sections (BNS / IPC / IT Act):
                </div>
                <div style={{ fontSize: '0.85rem', color: '#1e3a8a', marginTop: '0.2rem', fontWeight: 600 }}>
                  {analysis.ai_recommendations.legal_sections.join(' • ')}
                </div>
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.25rem' }}>
              <button
                className="btn btn-secondary"
                onClick={() => setShowReviewModal(false)}
                disabled={submitting}
              >
                Back to Edit
              </button>
              <button
                className="btn btn-primary"
                style={{ background: '#16a34a', borderColor: '#16a34a' }}
                onClick={handleFinalSubmit}
                disabled={submitting}
              >
                {submitting ? 'Registering Complaint…' : '✓ Confirm & Register FIR'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

