import React from 'react'

const URGENCY_CONFIG = {
  CRITICAL: {
    bg: '#fef2f2',
    color: '#991b1b',
    border: '#fca5a5',
    label: 'CRITICAL URGENCY',
  },
  HIGH: {
    bg: '#fffbeb',
    color: '#92400e',
    border: '#fcd34d',
    label: 'HIGH URGENCY',
  },
  MEDIUM: {
    bg: '#fefce8',
    color: '#854d0e',
    border: '#fef08a',
    label: 'MEDIUM URGENCY',
  },
  LOW: {
    bg: '#f0fdf4',
    color: '#166534',
    border: '#86efac',
    label: 'LOW URGENCY',
  },
  UNKNOWN: {
    bg: '#f8fafc',
    color: '#475569',
    border: '#cbd5e1',
    label: 'RETENTION UNKNOWN',
  },
}

export default function EvidenceUrgencyBadge({ urgency, confidence, showConfidence = true }) {
  const cfg = URGENCY_CONFIG[urgency?.toUpperCase()] || URGENCY_CONFIG.UNKNOWN

  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', flexWrap: 'wrap' }}>
      <span
        style={{
          background: cfg.bg,
          color: cfg.color,
          border: `1px solid ${cfg.border}`,
          fontSize: '0.72rem',
          fontWeight: 700,
          padding: '0.15rem 0.5rem',
          borderRadius: '4px',
          letterSpacing: '0.02em',
        }}
      >
        ⏱ {cfg.label}
      </span>

      {showConfidence && confidence && (
        <span
          style={{
            fontSize: '0.68rem',
            fontWeight: 600,
            padding: '0.15rem 0.4rem',
            borderRadius: '4px',
            background: confidence === 'VERIFIED' ? '#e0e7ff' : confidence === 'CONFIGURED' ? '#f3e8ff' : '#f1f5f9',
            color: confidence === 'VERIFIED' ? '#3730a3' : confidence === 'CONFIGURED' ? '#6b21a8' : '#64748b',
            border: `1px solid ${confidence === 'VERIFIED' ? '#c7d2fe' : confidence === 'CONFIGURED' ? '#e9d5ff' : '#e2e8f0'}`,
          }}
          title={confidence === 'CONFIGURED' ? 'Rule is prototype configured policy — verify local provider retention' : 'Source confidence'}
        >
          {confidence === 'VERIFIED' ? '✓ VERIFIED SOURCE' : confidence === 'CONFIGURED' ? '⚙ CONFIGURED (PROTOTYPE)' : '❓ UNKNOWN SOURCE'}
        </span>
      )}
    </div>
  )
}
