const STEPS = [
  { key: 'register', label: '1. Incident Statement' },
  { key: 'analysis', label: '2. AI Extraction' },
  { key: 'complete', label: '3. Follow-up Details' },
  { key: 'evidence', label: '4. Evidence' },
  { key: 'submit', label: '5. Confirm & Submit' },
]

export default function ProgressSteps({ currentStep = 'register' }) {
  const currentIndex = STEPS.findIndex((s) => s.key === currentStep)
  const activeIdx = currentIndex < 0 ? 0 : currentIndex

  return (
    <div className="progress-steps" style={{ marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.5rem' }}>
      {STEPS.map((step, i) => {
        const isDone = i < activeIdx
        const isCurrent = i === activeIdx
        const state = isDone ? 'complete' : isCurrent ? 'current' : ''
        return (
          <div key={step.key} className={`progress-step ${state}`} style={{ fontSize: '0.82rem' }}>
            <div className="progress-step-dot" style={{ fontSize: '0.75rem', fontWeight: 700 }}>
              {isDone ? '✓' : i + 1}
            </div>
            <div className="progress-step-label">{step.label}</div>
          </div>
        )
      })}
    </div>
  )
}

