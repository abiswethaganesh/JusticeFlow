import { useEffect, useState } from 'react'

const STAGES = ['Understanding incident', 'Identifying complaint type', 'Extracting relevant information']

export default function LoadingAnalysis() {
  const [activeIndex, setActiveIndex] = useState(0)

  useEffect(() => {
    // Purely cosmetic staged progression — the real work is one API
    // call, but this avoids a single opaque spinner.
    const interval = setInterval(() => {
      setActiveIndex((i) => Math.min(i + 1, STAGES.length - 1))
    }, 900)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="loading-analysis">
      <div className="loading-analysis-title">Analyzing your complaint…</div>
      {STAGES.map((stage, i) => {
        const state = i < activeIndex ? 'done' : i === activeIndex ? 'active' : ''
        return (
          <div key={stage} className={`loading-step ${state}`}>
            <span className="loading-step-marker">
              {i < activeIndex ? '✓' : i === activeIndex ? <span className="spinner" /> : '●'}
            </span>
            <span>{stage}</span>
          </div>
        )
      })}
    </div>
  )
}
