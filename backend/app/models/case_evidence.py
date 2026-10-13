from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CaseEvidence(Base):
    __tablename__ = "case_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(30), ForeignKey("complaints.case_id"), nullable=False, index=True)
    evidence_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "cctv" | "digital_transaction" | "telecom_cdr" | "document" | "photo" | etc.
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    file_path: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    file_url: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    source: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    incident_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    identified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    potentially_time_sensitive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    retention_period_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    retention_source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    retention_confidence: Mapped[str] = mapped_column(String(30), nullable=False, default="UNKNOWN")  # "VERIFIED" | "CONFIGURED" | "UNKNOWN"
    urgency: Mapped[str] = mapped_column(String(20), nullable=False, default="UNKNOWN")  # "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "UNKNOWN"
    estimated_expiry: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    preservation_status: Mapped[str] = mapped_column(String(50), nullable=False, default="NOT_REVIEWED")  # "NOT_REVIEWED" | "REVIEW_REQUIRED" | "PRESERVATION_RECOMMENDED" | "PRESERVATION_REQUESTED" | "PRESERVED" | "NOT_APPLICABLE" | "UNKNOWN"
    preservation_action_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    preservation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_digital_narrative_extracted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

