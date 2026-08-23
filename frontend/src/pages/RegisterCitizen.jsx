import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { getErrorMessage } from '../services/api'

export default function RegisterCitizen() {
  const { registerCitizen } = useAuth()
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [fullName, setFullName] = useState('')
  const [password, setPassword] = useState('')
  const [city, setCity] = useState('Chennai')

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!email || !email.includes('@')) {
      setError('Please enter a valid email address.')
      return
    }
    if (!phone || phone.length < 10) {
      setError('Please enter a valid mobile phone number.')
      return
    }
    if (!fullName.trim()) {
      setError('Please enter your full name.')
      return
    }
    if (!password || password.length < 6) {
      setError('Password must be at least 6 characters.')
      return
    }

    setLoading(true)
    setError(null)
    try {
      await registerCitizen({
        email: email.trim(),
        phone: phone.trim(),
        full_name: fullName.trim(),
        password,
        city: city.trim(),
      })
      navigate('/')
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to create citizen account.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: '440px', margin: '2.5rem auto' }}>
      <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.75rem', marginBottom: '0.5rem' }}>Citizen Registration</h1>
        <p style={{ color: 'var(--color-text-muted)', fontSize: '0.92rem' }}>
          Create your JusticeFlow citizen account to lodge and track complaints.
        </p>
      </div>

      <div className="card card-pad">
        {error && <div className="error-banner" style={{ marginBottom: '1rem' }}>{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="reg-email">Email Address *</label>
            <input
              id="reg-email"
              type="email"
              placeholder="e.g. rahul@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="field">
            <label htmlFor="reg-phone">Mobile Phone Number *</label>
            <input
              id="reg-phone"
              type="tel"
              placeholder="e.g. 9876543210"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              required
            />
          </div>

          <div className="field">
            <label htmlFor="reg-name">Full Name *</label>
            <input
              id="reg-name"
              type="text"
              placeholder="e.g. Rahul Kumar"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
            />
          </div>

          <div className="field">
            <label htmlFor="reg-pass">Password *</label>
            <input
              id="reg-pass"
              type="password"
              placeholder="At least 6 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <div className="field">
            <label htmlFor="reg-city">City / District</label>
            <input
              id="reg-city"
              type="text"
              placeholder="e.g. Chennai"
              value={city}
              onChange={(e) => setCity(e.target.value)}
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '1rem', justifyContent: 'center' }}
            disabled={loading}
          >
            {loading ? 'Creating Account…' : 'Register Citizen Account'}
          </button>
        </form>

        <div style={{ marginTop: '1.25rem', textAlign: 'center', fontSize: '0.88rem' }}>
          Already have an account?{' '}
          <Link to="/login" style={{ color: 'var(--color-primary)', fontWeight: 600, textDecoration: 'none' }}>
            Back to Login
          </Link>
        </div>
      </div>
    </div>
  )
}
