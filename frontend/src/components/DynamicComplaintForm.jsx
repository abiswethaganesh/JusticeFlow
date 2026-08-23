import React, { useState } from 'react'
import { FORM_SCHEMAS, FIELD_LABELS } from '../data/formSchemas'

export default function DynamicComplaintForm({
  complaintType = 'other',
  entities = {},
  missingFields = [],
  isCognizable = true,
  onEntityChange,
  readOnly = false,
}) {
  const schema = FORM_SCHEMAS[complaintType] || FORM_SCHEMAS.other
  const [editingField, setEditingField] = useState(null)

  const sections = schema.sections || [
    {
      id: 'general',
      title: 'Incident Details',
      fields: schema.requiredFields || ['complainant_name', 'incident_location', 'incident_date', 'description'],
    },
  ]

  const totalRequired = schema.requiredFields ? schema.requiredFields.length : 0
  const totalMissing = missingFields.length
  const totalCompleted = Math.max(0, totalRequired - totalMissing)

  const handleChange = (fieldKey, value) => {
    if (onEntityChange) {
      onEntityChange(fieldKey, value)
    }
  }

  return (
    <div
      className="case-review-panel"
      style={{
        background: '#ffffff',
        border: '1px solid var(--color-border)',
        borderRadius: '12px',
        overflow: 'hidden',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.03)',
      }}
    >
      {/* Panel Header */}
      <div
        style={{
          padding: '0.85rem 1.1rem',
          background: 'linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%)',
          borderBottom: '1px solid var(--color-border)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <span style={{ fontSize: '1.25rem' }}>{schema.icon || '📝'}</span>
          <div>
            <div style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-text-muted)', fontWeight: 700 }}>
              Case Information Review
            </div>
            <h3 style={{ fontSize: '0.98rem', margin: 0, color: 'var(--color-primary)', fontWeight: 700 }}>{schema.title}</h3>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span
            style={{
              fontSize: '0.72rem',
              fontWeight: 700,
              padding: '0.2rem 0.55rem',
              borderRadius: '20px',
              background: totalMissing === 0 ? '#ecfdf5' : '#fffbe6',
              color: totalMissing === 0 ? '#047857' : '#b45309',
              border: `1px solid ${totalMissing === 0 ? '#a7f3d0' : '#fde68a'}`,
            }}
          >
            {totalMissing === 0 ? '✓ Complete' : `${totalCompleted}/${totalRequired} Required`}
          </span>
          <span
            style={{
              fontSize: '0.68rem',
              fontWeight: 700,
              padding: '0.2rem 0.5rem',
              borderRadius: '4px',
              background: isCognizable ? '#fef2f2' : '#f0fdf4',
              color: isCognizable ? '#991b1b' : '#166534',
              border: `1px solid ${isCognizable ? '#fecaca' : '#bbf7d0'}`,
            }}
          >
            {isCognizable ? 'COGNIZABLE FIR' : 'NON-COGNIZABLE'}
          </span>
        </div>
      </div>

      {/* Scrollable Body showing ONLY relevant fields grouped by category */}
      <div
        style={{
          maxHeight: '400px',
          overflowY: 'auto',
          padding: '0.85rem 1rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.85rem',
        }}
      >
        {sections.map((section) => {
          const validFields = section.fields.filter((f) => schema.requiredFields.includes(f) || (schema.sections && schema.sections.some((s) => s.fields.includes(f))))
          if (validFields.length === 0) return null

          return (
            <div
              key={section.id}
              style={{
                background: '#f8fafc',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                padding: '0.75rem 0.85rem',
              }}
            >
              <div
                style={{
                  fontSize: '0.78rem',
                  fontWeight: 700,
                  color: '#334155',
                  marginBottom: '0.55rem',
                  textTransform: 'uppercase',
                  letterSpacing: '0.03em',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <span>{section.title}</span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.55rem' }}>
                {validFields.map((fieldKey) => {
                  const isRequired = schema.requiredFields.includes(fieldKey)
                  const isMissing = missingFields.includes(fieldKey)
                  const val = entities[fieldKey] ?? ''
                  const label = FIELD_LABELS[fieldKey] || fieldKey.replace(/_/g, ' ').toUpperCase()
                  const isEditing = editingField === fieldKey && !readOnly
                  const isTextArea = fieldKey === 'description' || fieldKey === 'stolen_items_description' || fieldKey === 'injury_details' || fieldKey === 'injury_or_damage_details' || fieldKey === 'accused_name_or_description'

                  return (
                    <div
                      key={fieldKey}
                      style={{
                        background: isMissing ? '#fff5f5' : '#ffffff',
                        border: `1px solid ${isMissing ? '#fecaca' : isEditing ? 'var(--color-primary)' : '#e2e8f0'}`,
                        borderRadius: '6px',
                        padding: '0.5rem 0.65rem',
                        transition: 'all 0.15s ease',
                      }}
                    >
                      <div
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          marginBottom: '0.2rem',
                        }}
                      >
                        <span style={{ fontSize: '0.74rem', fontWeight: 600, color: isMissing ? '#991b1b' : 'var(--color-text-muted)' }}>
                          {label} {isRequired && <span style={{ color: '#ef4444' }}>*</span>}
                        </span>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                          {isMissing ? (
                            <span style={{ fontSize: '0.66rem', color: '#dc2626', fontWeight: 700, background: '#fee2e2', padding: '0.1rem 0.35rem', borderRadius: '3px' }}>
                              Missing
                            </span>
                          ) : (
                            <span style={{ fontSize: '0.66rem', color: '#059669', fontWeight: 700, background: '#d1fae5', padding: '0.1rem 0.35rem', borderRadius: '3px' }}>
                              ✓ Complete
                            </span>
                          )}

                          {!readOnly && (
                            <button
                              type="button"
                              onClick={() => setEditingField(isEditing ? null : fieldKey)}
                              style={{
                                background: 'transparent',
                                border: 'none',
                                cursor: 'pointer',
                                fontSize: '0.72rem',
                                color: 'var(--color-primary)',
                                padding: '0 0.2rem',
                              }}
                              title="Edit Field"
                            >
                              {isEditing ? 'Done' : '✎ Edit'}
                            </button>
                          )}
                        </div>
                      </div>

                      {isEditing ? (
                        isTextArea ? (
                          <textarea
                            rows={2}
                            value={val}
                            autoFocus
                            placeholder={`Enter ${label.toLowerCase()}...`}
                            onChange={(e) => handleChange(fieldKey, e.target.value)}
                            onBlur={() => setEditingField(null)}
                            style={{
                              width: '100%',
                              padding: '0.35rem 0.5rem',
                              fontSize: '0.82rem',
                              borderRadius: '4px',
                              border: '1px solid var(--color-primary)',
                              background: '#ffffff',
                            }}
                          />
                        ) : (
                          <input
                            type="text"
                            value={val}
                            autoFocus
                            placeholder={`Enter ${label.toLowerCase()}...`}
                            onChange={(e) => handleChange(fieldKey, e.target.value)}
                            onBlur={() => setEditingField(null)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') setEditingField(null)
                            }}
                            style={{
                              width: '100%',
                              padding: '0.35rem 0.5rem',
                              fontSize: '0.82rem',
                              borderRadius: '4px',
                              border: '1px solid var(--color-primary)',
                              background: '#ffffff',
                            }}
                          />
                        )
                      ) : (
                        <div
                          onClick={() => !readOnly && setEditingField(fieldKey)}
                          style={{
                            fontSize: '0.83rem',
                            color: val ? '#0f172a' : '#94a3b8',
                            fontWeight: val ? 500 : 400,
                            fontStyle: val ? 'normal' : 'italic',
                            cursor: readOnly ? 'default' : 'pointer',
                            whiteSpace: 'pre-wrap',
                          }}
                        >
                          {val || '— Tap to enter value'}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
