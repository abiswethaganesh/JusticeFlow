import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import ProgressSteps from '../components/ProgressSteps'
import { FIELD_LABELS, FORM_SCHEMAS } from '../data/formSchemas'
import { useComplaintWorkflow } from '../context/ComplaintWorkflowContext'
import { useAuth } from '../context/AuthContext'
import { createComplaint, getErrorMessage } from '../services/api'

export default function ReviewComplaint() {
  const { workflow, updateWorkflow, getMergedEntities, resetWorkflow } = useComplaintWorkflow()
  const { user } = useAuth()
  const navigate = useNavigate()
  const analysis = workflow.analysis

  const initialEntities = useMemo(() => getMergedEntities(), []) // eslint-disable-line react-hooks/exhaustive-deps
  const [entities, setEntities] = useState(initialEntities)
  const [editing, setEditing] = useState(false)
  const [errors, setErrors] = useState({})
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState(null)
  const [submittedRecord, setSubmittedRecord] = useState(null)

  if (!analysis) {
    navigate('/register')
    return null
  }

  const schema = FORM_SCHEMAS[analysis.complaint_type] || FORM_SCHEMAS.other

  function handleFieldChange(field, value) {
    setEntities((prev) => ({ ...prev, [field]: value }))
    setErrors((prev) => ({ ...prev, [field]: null }))
  }

  function validateRequired() {
    const nextErrors = {}
    schema.requiredFields.forEach((field) => {
      if (!entities[field] || !String(entities[field]).trim()) {
        nextErrors[field] = 'This field is required.'
      }
    })
    return nextErrors
  }

  function handleSaveChanges() {
    const nextErrors = validateRequired()
    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors)
      return
    }
    updateWorkflow({ manualAnswers: { ...workflow.manualAnswers, ...entities } })
    setEditing(false)
  }

  async function handleSubmit() {
    const nextErrors = validateRequired()
    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors)
      setEditing(true)
      return
    }

    setSubmitting(true)
    setSubmitError(null)
    try {
      const record = await createComplaint({
        complaintType: analysis.complaint_type,
        complaintText: workflow.complaintText,
        summary: analysis.summary,
        structuredData: entities,
        citizenPhone: user?.phone || '',
      })
      updateWorkflow({ lastCaseId: record.case_id })
      setSubmittedRecord(record)
    } catch (err) {
      setSubmitError(getErrorMessage(err, 'Unable to submit your complaint right now.'))
    } finally {
      setSubmitting(false)
    }
  }

  if (submittedRecord) {
    return (
      <>
        <ProgressSteps currentStep="submit" />
        <div className="card success-panel">
          <div className="success-icon">✓</div>
          <h2>Complaint Submitted Successfully</h2>
          <div className="success-case-id">{submittedRecord.case_id}</div>
          <div
            style={{
              background: 'var(--color-bg-subtle, #f8fafc)',
              padding: '0.75rem 1rem',
              borderRadius: '8px',
              border: '1px solid var(--color-border)',
              margin: '1rem auto',
              maxWidth: '400px',
              fontSize: '0.88rem',
            }}
          >
            <div>
              <strong>Assigned Police Station:</strong>
            </div>
            <div style={{ fontSize: '0.98rem', color: 'var(--color-primary)', fontWeight: 600, marginTop: '0.2rem' }}>
              📍 {submittedRecord.assigned_station || 'General Police Station'}
            </div>
          </div>

          <p style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>Status: Submitted for Officer Review</p>
          <p style={{ marginTop: '0.9rem', maxWidth: '46ch', marginInline: 'auto' }}>
            Your complaint has been automatically routed to the station branch based on incident location.
          </p>
          <div className="btn-row" style={{ justifyContent: 'center', marginTop: '1.25rem' }}>
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
      </>
    )
  }

  return (
    <>
      <ProgressSteps currentStep="review" />

      <div className="page-header">
        <h1>Review Your Complaint</h1>
        <p>Check the details below before submitting for officer review. You can edit anything that looks wrong.</p>
      </div>

      <div className="card card-pad">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span className="eyebrow" style={{ marginBottom: 0 }}>
            {schema.title}
          </span>
          {!editing && (
            <button className="btn btn-ghost" onClick={() => setEditing(true)}>
              Edit
            </button>
          )}
        </div>

        <hr className="section-divider" />

        {editing ? (
          <>
            {schema.requiredFields.map((field) => (
              <div className={`field ${errors[field] ? 'has-error' : ''}`} key={field}>
                <label htmlFor={`review-${field}`}>{FIELD_LABELS[field] || field}</label>
                <input
                  id={`review-${field}`}
                  type="text"
                  value={entities[field] || ''}
                  onChange={(e) => handleFieldChange(field, e.target.value)}
                />
                {errors[field] && <div className="field-error">{errors[field]}</div>}
              </div>
            ))}
            <div className="btn-row">
              <button className="btn btn-primary" onClick={handleSaveChanges}>
                Save Changes
              </button>
              <button className="btn btn-ghost" onClick={() => setEditing(false)}>
                Cancel
              </button>
            </div>
          </>
        ) : (
          <>
            <div className="entity-grid">
              {schema.requiredFields.map((field) => (
                <div className="entity-item" key={field}>
                  <div className="entity-item-label">{FIELD_LABELS[field] || field}</div>
                  <div className="entity-item-value">{entities[field] || '—'}</div>
                </div>
              ))}
            </div>

            {submitError && <div className="error-banner">{submitError}</div>}

            <div className="btn-row">
              <button className="btn btn-primary" onClick={handleSubmit} disabled={submitting}>
                {submitting ? 'Submitting…' : 'Submit for Officer Review'}
              </button>
            </div>
          </>
        )}
      </div>
    </>
  )
}
