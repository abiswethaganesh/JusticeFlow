import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

const api = axios.create({ baseURL })

// Attach Bearer JWT or legacy auth headers to every request
api.interceptors.request.use((config) => {
  try {
    const saved = localStorage.getItem('justiceflow_user')
    if (saved) {
      const user = JSON.parse(saved)
      if (user.access_token) {
        config.headers['Authorization'] = `Bearer ${user.access_token}`
      }
      if (user.role) config.headers['X-User-Role'] = user.role
      if (user.phone) config.headers['X-User-Phone'] = user.phone
      if (user.id) config.headers['X-User-Id'] = user.id
      if (user.email) config.headers['X-User-Email'] = user.email
      if (user.station_branch) config.headers['X-Station-Branch'] = user.station_branch
    }
  } catch (e) {
    // ignore parse error
  }
  return config
})

// Authentication Endpoints
export async function loginUserApi({ login_identifier, password }) {
  const response = await api.post('/auth/login', { login_identifier, password })
  return response.data
}

export async function registerCitizenApi({ email, phone, full_name, password, city }) {
  const response = await api.post('/auth/register', { email, phone, full_name, password, city })
  return response.data
}

export async function legacyCitizenLoginApi({ phone, full_name, city }) {
  const response = await api.post('/auth/citizen/login', { phone, full_name, city })
  return response.data
}

export async function legacyOfficerLoginApi({ officer_id, name, station_branch, city }) {
  const response = await api.post('/auth/officer/login', { officer_id, name, station_branch, city })
  return response.data
}

// Conversational AI Intake API
export async function analyzeIntakeApi({ complaint_text, conversation_history = [], previous_entities = {} }) {
  const response = await api.post('/intake/analyze', {
    complaint_text,
    conversation_history,
    previous_entities,
  })
  return response.data
}

export async function analyzeComplaint(complaintText) {
  return analyzeIntakeApi({ complaint_text: complaintText })
}

// Evidence Upload API
export async function uploadEvidenceApi(formData) {
  const response = await api.post('/evidence/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

// Case / Complaint Endpoints
export async function createComplaintApi(payload) {
  const response = await api.post('/complaints', payload)
  return response.data
}

export async function createComplaint({ complaintType, complaintText, summary, structuredData, citizenPhone, assignedStation }) {
  return createComplaintApi({
    complaint_type: complaintType,
    complaint_text: complaintText,
    summary,
    structured_data: structuredData,
    citizen_phone: citizenPhone,
    assigned_station: assignedStation,
    incident_details: {
      location: structuredData?.incident_location || structuredData?.last_seen_location || '',
    },
    is_cognizable: true,
    priority: 'MEDIUM',
  })
}

export async function fetchComplaintsApi() {
  const response = await api.get('/complaints')
  return response.data
}

export async function deleteComplaintApi(caseId) {
  try {
    const response = await api.delete(`/complaints/${caseId}`)
    return response.data
  } catch (err) {
    if (err.response && err.response.status === 405) {
      const response = await api.post(`/complaints/${caseId}/delete`)
      return response.data
    }
    throw err
  }
}

export async function fetchComplaints() {
  return fetchComplaintsApi()
}

export async function fetchComplaintApi(caseId) {
  const response = await api.get(`/complaints/${caseId}`)
  return response.data
}

export async function fetchComplaint(caseId) {
  return fetchComplaintApi(caseId)
}

export async function updateComplaintStatusApi(caseId, status, remarks = '') {
  const response = await api.patch(`/complaints/${caseId}/status`, { status, remarks })
  return response.data
}

export async function updateComplaintStatus(caseId, status) {
  return updateComplaintStatusApi(caseId, status)
}

export async function fetchCaseEventsApi(caseId) {
  const response = await api.get(`/complaints/${caseId}/events`)
  return response.data
}

export async function fetchCaseEvidenceApi(caseId) {
  const response = await api.get(`/complaints/${caseId}/evidence`)
  return response.data
}

export async function deleteEvidenceApi(evidenceId) {
  const response = await api.delete(`/evidence/${evidenceId}`)
  return response.data
}

export async function fetchFIRDraftApi(caseId) {
  const response = await api.get(`/complaints/${caseId}/fir-draft`)
  return response.data
}

export async function registerFIRApi(caseId, iifData) {
  const response = await api.post(`/complaints/${caseId}/register-fir`, { iif_data: iifData })
  return response.data
}

export function getErrorMessage(err, fallback) {
  if (err?.response?.data?.detail) return err.response.data.detail
  if (err?.request) return 'Unable to connect to JusticeFlow API server. Please check your connection.'
  return fallback || 'Something went wrong. Please try again.'
}

export default api
