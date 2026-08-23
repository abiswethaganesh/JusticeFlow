import { createContext, useContext, useEffect, useState } from 'react'

const STORAGE_KEY = 'jf_workflow_core'

const ComplaintWorkflowContext = createContext(null)

function loadInitial() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return JSON.parse(raw)
  } catch {
    // corrupt/unavailable storage
  }
  return {
    complaintText: '',
    messages: [], // [{ id, sender: 'user'|'ai', text, timestamp }]
    analysis: null, // { complaint_type, is_cognizable, summary, entities, missing_fields, follow_up_questions, recommended_evidence, ai_recommendations }
    manualAnswers: {},
    evidenceFiles: [], // [{ id, title, type, file_url }]
    lastCaseId: null,
  }
}

export function ComplaintWorkflowProvider({ children }) {
  const [workflow, setWorkflow] = useState(loadInitial)

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(workflow))
    } catch {
      // ignore
    }
  }, [workflow])

  function updateWorkflow(patch) {
    setWorkflow((prev) => ({ ...prev, ...patch }))
  }

  function resetWorkflow() {
    try {
      localStorage.removeItem(STORAGE_KEY)
    } catch {
      // ignore
    }
    setWorkflow({
      complaintText: '',
      messages: [],
      analysis: null,
      manualAnswers: {},
      evidenceFiles: [],
      lastCaseId: null,
    })
  }

  function getMergedEntities() {
    return { ...(workflow.analysis?.entities || {}), ...workflow.manualAnswers }
  }

  return (
    <ComplaintWorkflowContext.Provider
      value={{ workflow, updateWorkflow, resetWorkflow, getMergedEntities }}
    >
      {children}
    </ComplaintWorkflowContext.Provider>
  )
}

export function useComplaintWorkflow() {
  const ctx = useContext(ComplaintWorkflowContext)
  if (!ctx) throw new Error('useComplaintWorkflow must be used within ComplaintWorkflowProvider')
  return ctx
}
