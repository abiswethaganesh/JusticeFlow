import { useState } from 'react'
import { Link } from 'react-router-dom'
import StatusBadge from './StatusBadge'

export default function ComplaintCard({ complaint, onDelete }) {
  const [confirming, setConfirming] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const handleDeleteClick = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setConfirming(true)
  }

  const handleConfirmDelete = async (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDeleting(true)
    try {
      if (onDelete) {
        await onDelete(complaint.id)
      }
    } finally {
      setDeleting(false)
      setConfirming(false)
    }
  }

  const handleCancelDelete = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setConfirming(false)
  }

  return (
    <div
      className="complaint-row"
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0.9rem 1.1rem',
        borderBottom: '1px solid var(--color-border)',
        textDecoration: 'none',
        color: 'inherit',
      }}
    >
      <Link
        to={`/status/${complaint.id}`}
        style={{
          display: 'flex',
          alignItems: 'center',
          flex: 1,
          justifyContent: 'space-between',
          textDecoration: 'none',
          color: 'inherit',
          marginRight: '1rem',
        }}
      >
        <div className="complaint-row-main">
          <span className="complaint-row-type" style={{ fontWeight: 600 }}>{complaint.typeLabel}</span>
          <span className="complaint-row-meta complaint-row-id" style={{ marginLeft: '0.6rem', color: 'var(--color-text-muted)', fontSize: '0.85rem' }}>
            #{complaint.id}
          </span>
        </div>

        <div className="complaint-row-right" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span className="complaint-row-date" style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)' }}>{complaint.date}</span>
          <StatusBadge status={complaint.status} />
        </div>
      </Link>

      {onDelete && (
        <div onClick={(e) => e.stopPropagation()}>
          {confirming ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <button
                type="button"
                className="btn"
                onClick={handleConfirmDelete}
                disabled={deleting}
                style={{
                  background: '#dc2626',
                  color: 'white',
                  border: 'none',
                  fontSize: '0.78rem',
                  padding: '0.35rem 0.65rem',
                  borderRadius: '4px',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                {deleting ? 'Deleting…' : 'Confirm'}
              </button>
              <button
                type="button"
                className="btn btn-ghost"
                onClick={handleCancelDelete}
                disabled={deleting}
                style={{
                  fontSize: '0.78rem',
                  padding: '0.35rem 0.5rem',
                }}
              >
                Cancel
              </button>
            </div>
          ) : (
            <button
              type="button"
              className="btn btn-ghost"
              onClick={handleDeleteClick}
              title="Delete complaint from your dashboard"
              style={{
                color: '#dc2626',
                borderColor: '#fca5a5',
                fontSize: '0.8rem',
                padding: '0.35rem 0.7rem',
                borderRadius: '6px',
                background: '#fef2f2',
                fontWeight: 600,
              }}
            >
              Delete Complaint
            </button>
          )}
        </div>
      )}
    </div>
  )
}
