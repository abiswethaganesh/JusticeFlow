from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CaseObligation(Base):
    """
    Model tracking active statutory and procedural obligations for a specific case.
    Stores start dates, calculated due dates, statuses, officer assignments, and escalation states.
    """
    __tablename__ = "case_obligations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(30), ForeignKey("complaints.case_id"), nullable=False, index=True)
    rule_id: Mapped[int] = mapped_column(Integer, ForeignKey("legal_procedure_rules.id"), nullable=False, index=True)

    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="UPCOMING", index=True
    )  # "UPCOMING" | "DUE_SOON" | "DUE_TODAY" | "OVERDUE" | "COMPLETED" | "WAIVED" | "NOT_APPLICABLE" | "REQUIRES_REVIEW"

    responsible_role: Mapped[str] = mapped_column(String(50), nullable=False, default="OFFICER")
    responsible_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    completion_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completion_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    reminder_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    escalation_status: Mapped[str] = mapped_column(String(30), nullable=False, default="NONE")  # "NONE" | "ALERT_SENT" | "ESCALATED_TO_SUPERVISOR"

    applicability_reason: Mapped[str] = mapped_column(Text, nullable=False)
    review_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
