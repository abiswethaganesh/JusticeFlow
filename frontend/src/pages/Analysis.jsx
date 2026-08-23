import { useNavigate } from 'react-router-dom'
import ProgressSteps from '../components/ProgressSteps'
import EntityCard from '../components/EntityCard'
import { MissingFieldFlag } from '../components/MissingFieldCard'
import { FORM_SCHEMAS, getMissingFields } from '../data/formSchemas'
import { useComplaintWorkflow } from '../context/ComplaintWorkflowContext'

function computeCompleteness(requiredCount, missingCount) {
  const presentRatio = (requiredCount - missingCount) / requiredCount
  if (presentRatio >= 0.7) return 'High'
  if (presentRatio >= 0.4) return 'Medium'
  return 'Low'
}

export default function Analysis() {
  const { workflow } = useComplaintWorkflow()
  const navigate = useNavigate()
  const analysis = workflow.analysis

  if (!analysis) {
    return (
      <div className="card card-pad">
        <p>No analysis yet. Start by describing an incident.</p>
        <div className="btn-row">
          <button className="btn btn-primary" onClick={() => navigate('/register')}>
            Register a Complaint
          </button>
        </div>
      </div>
    )
  }

  const schema = FORM_SCHEMAS[analysis.complaint_type] || FORM_SCHEMAS.other
  const entities = analysis.entities || {}
  const knownFields = Object.entries(entities).filter(([, v]) => v !== null && v !== undefined && String(v).trim() !== '')
  const missingFields = getMissingFields(analysis.complaint_type, entities)
  const completeness = computeCompleteness(schema.requiredFields.length, missingFields.length)

  function handleContinue() {
    navigate(missingFields.length > 0 ? '/complete' : '/review')
  }

  return (
    <>
      <ProgressSteps currentStep="analysis" />

      <div className="page-header">
        <h1>AI Complaint Analysis</h1>
      </div>

      <div className="card card-pad">
        <span className="eyebrow">Complaint Type</span>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
          <h2 style={{ fontSize: '1.3rem' }}>
            {schema.icon} {schema.title}
          </h2>
          <span className="confidence-tag">Fields identified: {completeness}</span>
        </div>

        <hr className="section-divider" />

        <span className="eyebrow">Case Summary</span>
        <p className="summary-quote">{analysis.summary}</p>

        <hr className="section-divider" />

        <span className="eyebrow">Information Identified</span>
        {knownFields.length > 0 ? (
          <div className="entity-grid">
            {knownFields.map(([field, value]) => (
              <EntityCard key={field} field={field} value={value} />
            ))}
          </div>
        ) : (
          <p style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>
            No details could be extracted automatically — you'll be asked for everything on the next step.
          </p>
        )}

        {missingFields.length > 0 && (
          <>
            <hr className="section-divider" />
            <span className="eyebrow">Information Required</span>
            {missingFields.map((field) => (
              <MissingFieldFlag key={field} field={field} />
            ))}
          </>
        )}

        <div className="btn-row">
          <button className="btn btn-primary" onClick={handleContinue}>
            Continue to Complete Complaint
          </button>
        </div>
      </div>
    </>
  )
}
