import { Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'
import Login from './pages/Login'
import RegisterCitizen from './pages/RegisterCitizen'
import Dashboard from './pages/Dashboard'
import ConversationalIntake from './pages/ConversationalIntake'
import RegisterComplaint from './pages/RegisterComplaint'
import Analysis from './pages/Analysis'
import CompleteComplaint from './pages/CompleteComplaint'
import ReviewComplaint from './pages/ReviewComplaint'
import CaseStatus from './pages/CaseStatus'
import OfficerDashboard from './pages/OfficerDashboard'

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register-citizen" element={<RegisterCitizen />} />

        <Route element={<Layout />}>
          {/* Citizen Routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute allowedRole="CITIZEN">
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/intake"
            element={
              <ProtectedRoute allowedRole="CITIZEN">
                <ConversationalIntake />
              </ProtectedRoute>
            }
          />
          <Route
            path="/register"
            element={
              <ProtectedRoute allowedRole="CITIZEN">
                <ConversationalIntake />
              </ProtectedRoute>
            }
          />
          <Route
            path="/analysis"
            element={
              <ProtectedRoute allowedRole="CITIZEN">
                <Analysis />
              </ProtectedRoute>
            }
          />
          <Route
            path="/complete"
            element={
              <ProtectedRoute allowedRole="CITIZEN">
                <CompleteComplaint />
              </ProtectedRoute>
            }
          />
          <Route
            path="/review"
            element={
              <ProtectedRoute allowedRole="CITIZEN">
                <ReviewComplaint />
              </ProtectedRoute>
            }
          />
          <Route
            path="/status/:caseId"
            element={
              <ProtectedRoute allowedRole="CITIZEN">
                <CaseStatus />
              </ProtectedRoute>
            }
          />

          {/* Officer Routes */}
          <Route
            path="/officer"
            element={
              <ProtectedRoute allowedRole="OFFICER">
                <OfficerDashboard />
              </ProtectedRoute>
            }
          />
        </Route>
      </Routes>
    </AuthProvider>
  )
}
