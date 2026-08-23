import { createContext, useContext, useState, useEffect } from 'react'
import { loginUserApi, registerCitizenApi, legacyCitizenLoginApi, legacyOfficerLoginApi } from '../services/api'

const AuthContext = createContext(null)

const STORAGE_KEY = 'justiceflow_user'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      return saved ? JSON.parse(saved) : null
    } catch {
      return null
    }
  })

  useEffect(() => {
    if (user) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(user))
    } else {
      localStorage.removeItem(STORAGE_KEY)
    }
  }, [user])

  const clearSessionData = () => {
    try {
      localStorage.removeItem('jf_workflow_core')
    } catch {
      // ignore
    }
  }

  const loginWithPassword = async (login_identifier, password) => {
    clearSessionData()
    const userData = await loginUserApi({ login_identifier, password })
    setUser(userData)
    return userData
  }

  const registerCitizen = async (formData) => {
    clearSessionData()
    const userData = await registerCitizenApi(formData)
    setUser(userData)
    return userData
  }

  const loginCitizenQuick = async (citizenData) => {
    clearSessionData()
    try {
      const userData = await legacyCitizenLoginApi(citizenData)
      setUser(userData)
      return userData
    } catch (e) {
      const fallback = {
        role: 'CITIZEN',
        phone: citizenData.phone,
        full_name: citizenData.full_name || 'Citizen',
        city: citizenData.city || 'Chennai',
        access_token: `token_${citizenData.phone}`,
      }
      setUser(fallback)
      return fallback
    }
  }

  const loginOfficerQuick = async (officerData) => {
    clearSessionData()
    try {
      const userData = await legacyOfficerLoginApi(officerData)
      setUser(userData)
      return userData
    } catch (e) {
      const fallback = {
        role: 'OFFICER',
        officer_id: officerData.officer_id,
        full_name: officerData.name || 'Officer',
        station_branch: officerData.station_branch || 'Anna Nagar Police Station',
        city: officerData.city || 'Chennai',
        access_token: `token_${officerData.officer_id}`,
      }
      setUser(fallback)
      return fallback
    }
  }

  const logout = () => {
    clearSessionData()
    setUser(null)
    localStorage.removeItem(STORAGE_KEY)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isCitizen: user?.role === 'CITIZEN',
        isOfficer: user?.role === 'OFFICER',
        loginWithPassword,
        registerCitizen,
        loginCitizenQuick,
        loginOfficerQuick,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
