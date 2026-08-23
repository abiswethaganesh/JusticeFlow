from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Integer, String, Text, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    
    citizen_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    citizen_phone: Mapped[str] = mapped_column(String(20), nullable=False, default="", index=True)

    complaint_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    workflow_type: Mapped[str] = mapped_column(String(50), nullable=False, default="cognizable_fir")
    
    original_complaint: Mapped[str] = mapped_column(Text, nullable=False)
    complaint_text: Mapped[str] = mapped_column(Text, nullable=False)  # backward compatible alias
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    
    structured_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    incident_details: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    police_station_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("police_stations.id"), nullable=True, index=True)
    assigned_station: Mapped[str] = mapped_column(String(100), nullable=False, default="Anna Nagar Police Station", index=True)
    
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="SUBMITTED", index=True)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIUM")
    is_cognizable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
