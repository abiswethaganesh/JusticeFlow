const STATUS_LABELS = {
  submitted: 'Submitted',
  under_review: 'Under Review',
  pending: 'Pending Review',
  resolved: 'Resolved',
  approved: 'Approved',
  potential_pattern: 'Potential Pattern',
}

export default function StatusBadge({ status }) {
  const label = STATUS_LABELS[status] || status
  return <span className={`status-badge status-${status}`}>{label}</span>
}
