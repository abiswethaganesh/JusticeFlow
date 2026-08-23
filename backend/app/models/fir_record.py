from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class FIRRecord(Base):
    __tablename__ = "fir_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(30), ForeignKey("complaints.case_id"), unique=True, nullable=False, index=True)
    fir_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    iif_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # IIF-I FIR structured format
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="DRAFT")  # DRAFT | VERIFIED_BY_OFFICER | REGISTERED_OFFICIAL
    registered_by_officer_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    official_cctns_ref_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
