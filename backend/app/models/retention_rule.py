from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EvidenceRetentionRule(Base):
    """
    Evidence Retention Knowledge Base Model.
    Stores retention policies backed by verified sources or explicitly marked CONFIGURED/PROTOTYPE.
    """
    __tablename__ = "evidence_retention_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evidence_type: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    display_label: Mapped[str] = mapped_column(String(100), nullable=False)
    retention_period_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # None if unknown
    source_policy: Mapped[str] = mapped_column(String(255), nullable=False)
    confidence_level: Mapped[str] = mapped_column(String(30), nullable=False, default="UNKNOWN")  # "VERIFIED" | "CONFIGURED" | "UNKNOWN"
    is_time_sensitive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    default_urgency: Mapped[str] = mapped_column(String(20), nullable=False, default="UNKNOWN")
    preservation_guidelines: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
