import { FIELD_LABELS, FIELD_QUESTIONS } from '../data/formSchemas'

export function MissingFieldFlag({ field }) {
  return (
    <div className="missing-field-item">
      <span>⚠</span>
      <span>{FIELD_LABELS[field] || field}</span>
    </div>
  )
}

export function MissingFieldInput({ field, value, error, onChange }) {
  return (
    <div className={`field ${error ? 'has-error' : ''}`}>
      <label htmlFor={`field-${field}`}>{FIELD_QUESTIONS[field] || `What is the ${FIELD_LABELS[field] || field}?`}</label>
      <input
        id={`field-${field}`}
        type="text"
        value={value || ''}
        onChange={(e) => onChange(field, e.target.value)}
        aria-invalid={!!error}
        aria-describedby={error ? `field-${field}-error` : undefined}
      />
      {error && (
        <div className="field-error" id={`field-${field}-error`}>
          {error}
        </div>
      )}
    </div>
  )
}
