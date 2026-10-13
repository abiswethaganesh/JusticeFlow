from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EvidenceAuditEvent(Base):
    """
    Audit Trail model recording every time-aware evidence action.
    Measures Time-to-Preservation-Request metric.
    """
    __tablename__ = "evidence_audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(30), ForeignKey("complaints.case_id"), nullable=False, index=True)
    evidence_id: Mapped[int] = mapped_column(Integer, ForeignKey("case_evidence.id"), nullable=False, index=True)

    action: Mapped[str] = mapped_column(String(100), nullable=False)  # "EVIDENCE_IDENTIFIED", "DRAFT_GENERATED", "PRESERVATION_REQUESTED", "PRESERVED", etc.
    previous_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    new_status: Mapped[str] = mapped_column(String(50), nullable=False)
    actor_name: Mapped[str] = mapped_column(String(100), nullable=False, default="System")
    actor_role: Mapped[str] = mapped_column(String(50), nullable=False, default="SYSTEM")
    time_to_preservation_minutes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
