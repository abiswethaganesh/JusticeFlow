from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ObligationAuditEvent(Base):
    """
    Audit Trail model recording every statutory obligation state transition,
    reminder, escalation, completion, or officer review action.
    """
    __tablename__ = "obligation_audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    obligation_id: Mapped[int] = mapped_column(Integer, ForeignKey("case_obligations.id"), nullable=False, index=True)
    case_id: Mapped[str] = mapped_column(String(30), ForeignKey("complaints.case_id"), nullable=False, index=True)

    action: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "OBLIGATION_CREATED" | "OBLIGATION_REVIEW_REQUIRED" | "STATUS_UPDATED" | "REMINDER_SENT" | "ESCALATION_TRIGGERED" | "COMPLETED" | "WAIVED" | "MARKED_NOT_APPLICABLE" | "RULE_REVIEWED"

    previous_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    new_status: Mapped[str] = mapped_column(String(30), nullable=False)

    actor_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    actor_name: Mapped[str] = mapped_column(String(100), nullable=False, default="System")
    actor_role: Mapped[str] = mapped_column(String(50), nullable=False, default="SYSTEM")
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
