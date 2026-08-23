import { useState } from 'react'
import { registerFIRApi, getErrorMessage } from '../services/api'

export default function FIRDraftViewer({ caseId, initialFIRDraft, onFIRRegistered }) {
  const [firData, setFirData] = useState(initialFIRDraft || {})
  const [editing, setEditing] = useState(false)
  const [registering, setRegistering] = useState(false)
  const [registerError, setRegisterError] = useState(null)
  const [registeredResult, setRegisteredResult] = useState(null)

  const handleFieldChange = (section, key, value) => {
    if (section) {
      setFirData((prev) => ({
        ...prev,
        [section]: {
          ...(prev[section] || {}),
          [key]: value,
        },
      }))
    } else {
      setFirData((prev) => ({ ...prev, [key]: value }))
    }
  }

  const handleRegisterCCTNS = async () => {
    setRegistering(true)
    setRegisterError(null)
    try {
      const res = await registerFIRApi(caseId, firData)
      setRegisteredResult(res)
      if (onFIRRegistered) onFIRRegistered(res)
    } catch (err) {
      setRegisterError(getErrorMessage(err, 'Failed to register FIR in Official CCTNS System.'))
    } finally {
      setRegistering(false)
    }
  }

  return (
    <div
      className="card card-pad"
      style={{
        border: '2px solid var(--color-primary, #3b82f6)',
        marginTop: '1.5rem',
        background: '#f8fafc',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <span
            style={{
              background: '#ef4444',
              color: 'white',
              fontSize: '0.75rem',
              fontWeight: 700,
              padding: '0.2rem 0.5rem',
              borderRadius: '4px',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            AI-Assisted FIR Draft – Requires Officer Verification
          </span>
          <h2 style={{ fontSize: '1.2rem', marginTop: '0.5rem' }}>
            Form IIF-I — First Information Report (Draft)
          </h2>
        </div>
        <div>
          {!editing ? (
            <button className="btn btn-ghost" style={{ fontSize: '0.8rem' }} onClick={() => setEditing(true)}>
              Edit FIR Draft
            </button>
          ) : (
            <button className="btn btn-primary" style={{ fontSize: '0.8rem' }} onClick={() => setEditing(false)}>
              Save Draft Edits
            </button>
          )}
        </div>
      </div>

      <hr className="section-divider" />

      {registeredResult && (
        <div
          style={{
            background: '#ecfdf5',
            border: '1px solid #10b981',
            borderRadius: '8px',
            padding: '1rem',
            marginBottom: '1.25rem',
          }}
        >
          <div style={{ color: '#047857', fontWeight: 700, fontSize: '1.05rem' }}>
            FIR Officially Registered in Police System (CCTNS Adapter)
          </div>
          <div style={{ marginTop: '0.5rem', fontSize: '0.9rem' }}>
            <strong>Official CCTNS Reference ID:</strong>{' '}
            <span className="case-id-mono" style={{ background: 'white', padding: '0.2rem 0.5rem', borderRadius: '4px' }}>
              {registeredResult.official_cctns_ref_id}
            </span>
          </div>
          <div style={{ fontSize: '0.85rem', color: '#065f46', marginTop: '0.3rem' }}>
            FIR Number: <strong>{registeredResult.fir_number}</strong> | Status: REGISTERED_OFFICIAL
          </div>
        </div>
      )}

      {registerError && <div className="error-banner" style={{ marginBottom: '1rem' }}>{registerError}</div>}

      {/* IIF-I Form Structure */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem', marginBottom: '1.25rem' }}>
        <div className="entity-item">
          <div className="entity-item-label">1. District & Police Station</div>
          <div className="entity-item-value">
            {editing ? (
              <input
                type="text"
                value={firData.police_station || ''}
                onChange={(e) => handleFieldChange(null, 'police_station', e.target.value)}
                style={{ width: '100%', padding: '0.4rem', fontSize: '0.85rem' }}
              />
            ) : (
              `${firData.district || 'Chennai District'} — ${firData.police_station || 'Police Station'}`
            )}
          </div>
        </div>

        <div className="entity-item">
          <div className="entity-item-label">2. Date & Time of Occurrence</div>
          <div className="entity-item-value">
            {editing ? (
              <input
                type="text"
                value={firData.occurrence_date_time || ''}
                onChange={(e) => handleFieldChange(null, 'occurrence_date_time', e.target.value)}
                style={{ width: '100%', padding: '0.4rem', fontSize: '0.85rem' }}
              />
            ) : (
              firData.occurrence_date_time || '—'
            )}
          </div>
        </div>

        <div className="entity-item">
          <div className="entity-item-label">3. Acts & Sections (BNS / IPC / IT Act)</div>
          <div className="entity-item-value">
            {Array.isArray(firData.acts_and_sections)
              ? firData.acts_and_sections.join(', ')
              : String(firData.acts_and_sections || 'BNS Section 303(2) Theft')}
          </div>
        </div>

        <div className="entity-item">
          <div className="entity-item-label">4. Place of Occurrence</div>
          <div className="entity-item-value">{firData.place_of_occurrence || '—'}</div>
        </div>
      </div>

      {/* Complainant Details */}
      <div style={{ marginBottom: '1.25rem' }}>
        <span className="eyebrow">5. Complainant Information</span>
        <div className="entity-grid" style={{ marginTop: '0.4rem' }}>
          <div className="entity-item">
            <div className="entity-item-label">Complainant Name</div>
            <div className="entity-item-value">{firData.complainant_details?.name || '—'}</div>
          </div>
          <div className="entity-item">
            <div className="entity-item-label">Contact Number</div>
            <div className="entity-item-value">{firData.complainant_details?.phone || '—'}</div>
          </div>
          <div className="entity-item">
            <div className="entity-item-label">Address</div>
            <div className="entity-item-value">{firData.complainant_details?.address || '—'}</div>
          </div>
        </div>
      </div>

      {/* Accused & Stolen Property Details */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem', marginBottom: '1.25rem' }}>
        <div className="entity-item">
          <div className="entity-item-label">6. Suspect / Accused Details</div>
          <div className="entity-item-value">{firData.suspect_accused_details || 'Unknown Person(s)'}</div>
        </div>
        <div className="entity-item">
          <div className="entity-item-label">7. Particulars of Stolen / Involved Property</div>
          <div className="entity-item-value">{firData.stolen_or_involved_property || '—'}</div>
        </div>
      </div>

      {/* Formal FIR Narrative Statement */}
      <div style={{ marginBottom: '1.5rem' }}>
        <span className="eyebrow">8. Formal Statement of Facts (FIR Narrative)</span>
        {editing ? (
          <textarea
            rows={5}
            value={firData.fir_narrative || ''}
            onChange={(e) => handleFieldChange(null, 'fir_narrative', e.target.value)}
            style={{ width: '100%', padding: '0.6rem', fontSize: '0.88rem', borderRadius: '6px', border: '1px solid var(--color-border)' }}
          />
        ) : (
          <div
            style={{
              background: 'white',
              padding: '0.9rem',
              borderRadius: '6px',
              border: '1px solid var(--color-border)',
              fontSize: '0.88rem',
              lineHeight: 1.5,
              whiteSpace: 'pre-wrap',
            }}
          >
            {firData.fir_narrative || 'Detailed statement of facts for FIR entry.'}
          </div>
        )}
      </div>

      {/* Official CCTNS Action Bar */}
      {!registeredResult && (
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', alignItems: 'center' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
            Official action requires officer verification.
          </span>
          <button
            className="btn btn-primary"
            style={{ background: '#0284c7', borderColor: '#0284c7' }}
            onClick={handleRegisterCCTNS}
            disabled={registering}
          >
            {registering ? 'Submitting to CCTNS…' : 'Register FIR in Official System (CCTNS)'}
          </button>
        </div>
      )}
    </div>
  )
}
