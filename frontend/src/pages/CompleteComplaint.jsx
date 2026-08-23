import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import ProgressSteps from '../components/ProgressSteps'
import { MissingFieldInput } from '../components/MissingFieldCard'
import { getMissingFields } from '../data/formSchemas'
import { useComplaintWorkflow } from '../context/ComplaintWorkflowContext'

export default function CompleteComplaint() {
  const { workflow, updateWorkflow, getMergedEntities } = useComplaintWorkflow()
  const navigate = useNavigate()
  const analysis = workflow.analysis

  const missingFields = analysis ? getMissingFields(analysis.complaint_type, getMergedEntities()) : []
  const [answers, setAnswers] = useState(workflow.manualAnswers || {})
  const [errors, setErrors] = useState({})

  if (!analysis) {
    navigate('/register')
    return null
  }

  function handleChange(field, value) {
    setAnswers((prev) => ({ ...prev, [field]: value }))
    setErrors((prev) => ({ ...prev, [field]: null }))
  }

  function handleContinue() {
    const nextErrors = {}
    missingFields.forEach((field) => {
      if (!answers[field] || !answers[field].trim()) {
        nextErrors[field] = 'This field is required.'
      }
    })
    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors)
      return
    }
    updateWorkflow({ manualAnswers: { ...workflow.manualAnswers, ...answers } })
    navigate('/review')
  }

  return (
    <>
      <ProgressSteps currentStep="complete" />

      <div className="page-header">
        <h1>Additional Information Required</h1>
        <p>
          Your complaint is almost ready. We need {missingFields.length} more detail
          {missingFields.length === 1 ? '' : 's'} before it can be submitted.
        </p>
      </div>

      <div className="card card-pad">
        {missingFields.length === 0 ? (
          <p>All required information has been collected.</p>
        ) : (
          missingFields.map((field) => (
            <MissingFieldInput
              key={field}
              field={field}
              value={answers[field]}
              error={errors[field]}
              onChange={handleChange}
            />
          ))
        )}

        <div className="btn-row">
          <button className="btn btn-primary" onClick={handleContinue}>
            Continue
          </button>
        </div>
      </div>
    </>
  )
}
