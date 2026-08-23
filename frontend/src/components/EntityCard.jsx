import { FIELD_LABELS } from '../data/formSchemas'

export default function EntityCard({ field, value }) {
  return (
    <div className="entity-item">
      <div className="entity-item-label">{FIELD_LABELS[field] || field}</div>
      <div className="entity-item-value">{value}</div>
    </div>
  )
}
