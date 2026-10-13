import React, { useState } from 'react'

export function StatusBadge({ status, escalationStatus }) {
  const configs = {
    OVERDUE: {
      bg: '#FCEAEA',
      color: '#B3261E',
      border: '#F5C6C6',
      label: 'OVERDUE',
    },
    DUE_TODAY: {
      bg: '#FDF1DD',
      color: '#A15C00',
      border: '#F8D8A8',
      label: 'DUE TODAY',
    },
    DUE_SOON: {
      bg: '#FDF1DD',
      color: '#8A4F00',
      border: '#F8D8A8',
      label: 'DUE SOON',
    },
    UPCOMING: {
      bg: '#E9F0FD',
      color: '#17395E',
      border: '#C2D7F9',
      label: 'UPCOMING',
    },
    COMPLETED: {
      bg: '#E7F6EC',
      color: '#157F3C',
      border: '#B6E6C5',
      label: 'COMPLETED',
    },
    REQUIRES_REVIEW: {
      bg: '#F3E8FF',
      color: '#6B21A8',
      border: '#E9D5FF',
      label: 'REQUIRES REVIEW',
    },
    NOT_APPLICABLE: {
      bg: '#F1F5F9',
      color: '#475569',
      border: '#E2E8F0',
      label: 'EXEMPT',
    },
  }

  const cfg = configs[status] || {
    bg: '#F1F5F9',
    color: '#475569',
    border: '#E2E8F0',
    label: status || 'UNKNOWN',
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: '0.2rem' }}>
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.35rem',
          padding: '0.15rem 0.55rem',
          borderRadius: '999px',
          fontSize: '0.72rem',
          fontWeight: 600,
          background: cfg.bg,
          color: cfg.color,
          border: `1px solid ${cfg.border}`,
          lineHeight: '1.2',
        }}
      >
        <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: cfg.color, display: 'inline-block' }} />
        {cfg.label}
      </span>
      {escalationStatus === 'ESCALATED_TO_SUPERVISOR' && status === 'OVERDUE' && (
        <span
          style={{
            fontSize: '0.68rem',
            fontWeight: 700,
            color: '#B3261E',
            background: '#FCEAEA',
            border: '1px solid #F5C6C6',
            borderRadius: '4px',
            padding: '0.1rem 0.4rem',
          }}
        >
          Escalated to Supervisor
        </span>
      )}
    </div>
  )
}

function RemainingTimeIndicator({ obligation }) {
  const isQualitative = obligation.rule?.deadline_unit === 'QUALITATIVE' || !obligation.due_date

  if (isQualitative) {
    return <span style={{ fontSize: '0.78rem', color: '#5C6773', fontWeight: 500 }}>Procedural monitoring</span>
  }

  if (obligation.status === 'COMPLETED') {
    return <span style={{ fontSize: '0.78rem', color: '#157F3C', fontWeight: 600 }}>Completed</span>
  }

  if (obligation.status === 'NOT_APPLICABLE') {
    return <span style={{ fontSize: '0.78rem', color: '#8994A1', fontWeight: 500 }}>Exempt</span>
  }

  if (obligation.status === 'OVERDUE') {
    const days = obligation.days_overdue || 1
    return <span style={{ fontSize: '0.78rem', color: '#B3261E', fontWeight: 700 }}>{days} day{days > 1 ? 's' : ''} overdue</span>
  }

  if (obligation.status === 'DUE_TODAY') {
    return <span style={{ fontSize: '0.78rem', color: '#A15C00', fontWeight: 700 }}>Due Today</span>
  }

  const days = obligation.days_remaining ?? 0
  const color = obligation.status === 'DUE_SOON' ? '#A15C00' : '#16202B'

  return <span style={{ fontSize: '0.78rem', color, fontWeight: 500 }}>{days} day{days !== 1 ? 's' : ''} remaining</span>
}

export default function StatutoryObligationPanel({ obligations = [], onSelectObligation, isLoading = false }) {
  const [filter, setFilter] = useState('ALL')

  const totalCount = obligations.length
  const dueSoonCount = obligations.filter((i) => ['DUE_TODAY', 'DUE_SOON'].includes(i.status)).length
  const overdueCount = obligations.filter((i) => i.status === 'OVERDUE').length
  const reviewCount = obligations.filter((i) => i.status === 'REQUIRES_REVIEW').length

  const filteredObligations = obligations.filter((item) => {
    if (filter === 'ALL') return true
    if (filter === 'DUE_SOON') return ['DUE_TODAY', 'DUE_SOON'].includes(item.status)
    if (filter === 'OVERDUE') return item.status === 'OVERDUE'
    if (filter === 'REVIEW') return item.status === 'REQUIRES_REVIEW'
    if (filter === 'COMPLETED') return item.status === 'COMPLETED'
    return true
  })

  return (
    <div
      style={{
        background: '#EBF3FA',
        border: '1px solid #CBD7E6',
        borderLeft: '4px solid #0F2A4A',
        borderRadius: '14px',
        padding: '1.25rem',
        marginBottom: '1.75rem',
        width: '100%',
        boxShadow: '0 2px 8px rgba(15, 42, 74, 0.05)',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justify: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '0.5rem',
          marginBottom: '1rem',
        }}
      >
        <div>
          <h3
            style={{
              fontSize: '1rem',
              fontWeight: 700,
              color: '#0F2A4A',
              letterSpacing: '0.02em',
              textTransform: 'uppercase',
            }}
          >
            STATUTORY &amp; PROCEDURAL OBLIGATIONS
          </h3>
          <p style={{ fontSize: '0.8rem', color: '#395778', marginTop: '0.15rem', fontWeight: 500 }}>
            Verified procedural obligations &amp; accountability tracking
          </p>
        </div>

        <div style={{ fontSize: '0.78rem', color: '#395778', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
          {filteredObligations.length} of {totalCount} Mandates
        </div>
      </div>

      {/* Summary Statistics Row */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
          gap: '0.75rem',
          marginBottom: '1rem',
        }}
      >
        <button
          type="button"
          onClick={() => setFilter('ALL')}
          style={{
            background: '#FFFFFF',
            border: filter === 'ALL' ? '2px solid #0F2A4A' : '1px solid #CBD7E6',
            borderRadius: '10px',
            padding: '0.75rem 0.9rem',
            textAlign: 'left',
            transition: 'all 0.15s ease',
          }}
        >
          <div style={{ fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase', color: '#5C6773', letterSpacing: '0.04em' }}>
            Total Obligations
          </div>
          <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#0F2A4A', marginTop: '0.2rem' }}>
            {totalCount}
          </div>
        </button>

        <button
          type="button"
          onClick={() => setFilter('DUE_SOON')}
          style={{
            background: '#FFFFFF',
            border: filter === 'DUE_SOON' ? '2px solid #A15C00' : '1px solid #CBD7E6',
            borderRadius: '10px',
            padding: '0.75rem 0.9rem',
            textAlign: 'left',
            transition: 'all 0.15s ease',
          }}
        >
          <div style={{ fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase', color: '#A15C00', letterSpacing: '0.04em' }}>
            Due Soon
          </div>
          <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#A15C00', marginTop: '0.2rem' }}>
            {dueSoonCount}
          </div>
        </button>

        <button
          type="button"
          onClick={() => setFilter('OVERDUE')}
          style={{
            background: '#FFFFFF',
            border: filter === 'OVERDUE' ? '2px solid #B3261E' : '1px solid #CBD7E6',
            borderRadius: '10px',
            padding: '0.75rem 0.9rem',
            textAlign: 'left',
            transition: 'all 0.15s ease',
          }}
        >
          <div style={{ fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase', color: '#B3261E', letterSpacing: '0.04em' }}>
            Overdue
          </div>
          <div style={{ fontSize: '1.35rem', fontWeight: 800, color: overdueCount > 0 ? '#B3261E' : '#0F2A4A', marginTop: '0.2rem' }}>
            {overdueCount}
          </div>
        </button>

        <button
          type="button"
          onClick={() => setFilter('REVIEW')}
          style={{
            background: '#FFFFFF',
            border: filter === 'REVIEW' ? '2px solid #6B21A8' : '1px solid #CBD7E6',
            borderRadius: '10px',
            padding: '0.75rem 0.9rem',
            textAlign: 'left',
            transition: 'all 0.15s ease',
          }}
        >
          <div style={{ fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase', color: '#6B21A8', letterSpacing: '0.04em' }}>
            Requires Review
          </div>
          <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#6B21A8', marginTop: '0.2rem' }}>
            {reviewCount}
          </div>
        </button>
      </div>

      {/* Main Table White Container */}
      {isLoading ? (
        <div
          style={{
            background: '#FFFFFF',
            borderRadius: '10px',
            border: '1px solid #CBD7E6',
            padding: '2rem',
            textAlign: 'center',
            color: '#5C6773',
            fontSize: '0.85rem',
          }}
        >
          Loading statutory obligations...
        </div>
      ) : filteredObligations.length === 0 ? (
        <div
          style={{
            background: '#FFFFFF',
            borderRadius: '10px',
            border: '1px solid #CBD7E6',
            padding: '2rem',
            textAlign: 'center',
            color: '#5C6773',
            fontSize: '0.85rem',
          }}
        >
          No statutory obligations matching current filter.
        </div>
      ) : (
        <div
          style={{
            background: '#FFFFFF',
            borderRadius: '10px',
            border: '1px solid #CBD7E6',
            overflowX: 'auto',
            boxShadow: '0 1px 3px rgba(15, 42, 74, 0.04)',
          }}
        >
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem', textAlign: 'left' }}>
            <thead>
              <tr style={{ background: '#F4F7FA', borderBottom: '1px solid #E1E5EB' }}>
                <th style={{ padding: '0.65rem 0.85rem', fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', color: '#5C6773', letterSpacing: '0.04em' }}>Case ID</th>
                <th style={{ padding: '0.65rem 0.85rem', fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', color: '#5C6773', letterSpacing: '0.04em' }}>Obligation</th>
                <th style={{ padding: '0.65rem 0.85rem', fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', color: '#5C6773', letterSpacing: '0.04em' }}>Section</th>
                <th style={{ padding: '0.65rem 0.85rem', fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', color: '#5C6773', letterSpacing: '0.04em' }}>Due Date</th>
                <th style={{ padding: '0.65rem 0.85rem', fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', color: '#5C6773', letterSpacing: '0.04em' }}>Countdown</th>
                <th style={{ padding: '0.65rem 0.85rem', fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', color: '#5C6773', letterSpacing: '0.04em' }}>Status</th>
                <th style={{ padding: '0.65rem 0.85rem', fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', color: '#5C6773', letterSpacing: '0.04em', textAlign: 'right' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredObligations.map((ob, idx) => {
                const isQualitative = ob.rule?.deadline_unit === 'QUALITATIVE' || !ob.due_date

                return (
                  <tr
                    key={ob.id}
                    style={{
                      borderBottom: idx === filteredObligations.length - 1 ? 'none' : '1px solid #E1E5EB',
                      background: '#FFFFFF',
                    }}
                  >
                    <td style={{ padding: '0.75rem 0.85rem', whiteSpace: 'nowrap' }}>
                      <span
                        style={{
                          fontFamily: 'var(--font-mono)',
                          fontSize: '0.78rem',
                          fontWeight: 700,
                          color: '#0F2A4A',
                          background: '#F0F4F8',
                          padding: '0.2rem 0.45rem',
                          borderRadius: '4px',
                          border: '1px solid #D0DFEE',
                        }}
                      >
                        {ob.case_id}
                      </span>
                    </td>

                    <td style={{ padding: '0.75rem 0.85rem', maxWidth: '280px' }}>
                      <div style={{ fontWeight: 600, color: '#0F2A4A', fontSize: '0.82rem', lineHeight: '1.3' }}>
                        {ob.rule?.title || 'Statutory Obligation'}
                      </div>
                    </td>

                    <td style={{ padding: '0.75rem 0.85rem', whiteSpace: 'nowrap' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: '#245789', fontWeight: 600 }}>
                        {ob.rule?.legal_source} — {ob.rule?.section_reference}
                      </span>
                    </td>

                    <td style={{ padding: '0.75rem 0.85rem', whiteSpace: 'nowrap' }}>
                      {isQualitative ? (
                        <span style={{ color: '#5C6773', fontStyle: 'italic', fontSize: '0.78rem' }}>No Fixed Numeric Due Date</span>
                      ) : (
                        <span style={{ fontWeight: 600, color: ob.status === 'OVERDUE' ? '#B3261E' : '#0F2A4A', fontSize: '0.78rem' }}>
                          {new Date(ob.due_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                        </span>
                      )}
                    </td>

                    <td style={{ padding: '0.75rem 0.85rem', whiteSpace: 'nowrap' }}>
                      <RemainingTimeIndicator obligation={ob} />
                    </td>

                    <td style={{ padding: '0.75rem 0.85rem', whiteSpace: 'nowrap' }}>
                      <StatusBadge status={ob.status} escalationStatus={ob.escalation_status} />
                    </td>

                    <td style={{ padding: '0.75rem 0.85rem', textAlign: 'right', whiteSpace: 'nowrap' }}>
                      <button
                        type="button"
                        onClick={() => onSelectObligation(ob)}
                        style={{
                          background: '#0F2A4A',
                          color: '#FFFFFF',
                          border: 'none',
                          borderRadius: '6px',
                          padding: '0.35rem 0.7rem',
                          fontSize: '0.78rem',
                          fontWeight: 600,
                          cursor: 'pointer',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.25rem',
                          boxShadow: '0 1px 2px rgba(15, 42, 74, 0.1)',
                        }}
                      >
                        View &amp; Action &rsaquo;
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
