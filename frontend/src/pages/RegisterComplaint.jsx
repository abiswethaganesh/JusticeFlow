import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import ProgressSteps from '../components/ProgressSteps'
import LoadingAnalysis from '../components/LoadingAnalysis'
import { analyzeComplaint, getErrorMessage } from '../services/api'
import { useComplaintWorkflow } from '../context/ComplaintWorkflowContext'

const MAX_LENGTH = 2000

export default function RegisterComplaint() {
  const { workflow, updateWorkflow } = useComplaintWorkflow()
  const [text, setText] = useState(workflow.complaintText || '')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  async function handleAnalyze() {
    if (!text.trim()) {
      setError('Please describe what happened before analyzing.')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const result = await analyzeComplaint(text)
      updateWorkflow({ complaintText: text, analysis: result, manualAnswers: {} })
      navigate('/analysis')
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to analyze the complaint right now.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <ProgressSteps currentStep="describe" />

      <div className="page-header">
        <h1>Register a Complaint</h1>
        <p>
          Describe the incident in your own words. You do not need to know the official complaint
          format — JusticeFlow will identify the relevant information and guide you through the
          required details.
        </p>
      </div>

      <div className="card card-pad">
        {loading ? (
          <LoadingAnalysis />
        ) : (
          <>
            <div className="field" style={{ marginBottom: '0.4rem' }}>
              <label htmlFor="complaint-text">Incident Description</label>
              <textarea
                id="complaint-text"
                rows={7}
                maxLength={MAX_LENGTH}
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Example: My Honda Activa was stolen yesterday evening near my college parking area..."
              />
              <div className="char-counter">
                {text.length} / {MAX_LENGTH}
              </div>
            </div>

            {error && <div className="error-banner">{error}</div>}

            <div className="btn-row">
              <button className="btn btn-primary" onClick={handleAnalyze} disabled={loading}>
                Analyze Complaint
              </button>
            </div>
          </>
        )}
      </div>
    </>
  )
}
