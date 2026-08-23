const STAGES = [
  { key: 'submitted', label: 'Complaint Submitted' },
  { key: 'verified', label: 'Information Verified' },
  { key: 'officer_review', label: 'Officer Review' },
  { key: 'investigation', label: 'Investigation' },
  { key: 'updated', label: 'Case Updated' },
]

export default function CaseTimeline({ currentStage, submittedAt }) {
  const currentIndex = STAGES.findIndex((s) => s.key === currentStage)
  return (
    <div className="case-timeline">
      {STAGES.map((stage, i) => {
        const state = i < currentIndex ? 'complete' : i === currentIndex ? 'current' : ''
        return (
          <div key={stage.key} className={`timeline-item ${state}`}>
            <div className="timeline-marker" />
            <div>
              <div className="timeline-content-title">{stage.label}</div>
              {i === 0 && submittedAt && <div className="timeline-content-meta">{submittedAt}</div>}
              {i === currentIndex && i !== 0 && (
                <div className="timeline-content-meta">Current stage</div>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
