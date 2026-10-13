from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class LegalProcedureRule(Base):
    """
    Knowledge Base table storing verified statutory and procedural rules (e.g. BNSS 2023).
    Ensures deterministic rule applicability and prevents AI hallucination of legal deadlines.
    """
    __tablename__ = "legal_procedure_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rule_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)  # e.g., "BNSS_193_1", "BNSS_193_2", "BNSS_193_3_II"
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    legal_source: Mapped[str] = mapped_column(String(150), nullable=False)  # "Bharatiya Nagarik Suraksha Sanhita, 2023"
    section_reference: Mapped[str] = mapped_column(String(50), nullable=False)  # "Section 193(1)", "Section 193(2)", "Section 193(3)(ii)"
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    applicability_conditions: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # {"target_bns_sections": ["64","65",...], "target_pocso_sections": ["4","6",...]}
    deadline_value: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # e.g. 2, 90, or None
    deadline_unit: Mapped[str] = mapped_column(String(20), nullable=False, default="QUALITATIVE")  # "DAYS" | "MONTHS" | "NONE" | "QUALITATIVE"
    start_event: Mapped[str] = mapped_column(String(100), nullable=False, default="CASE_INFORMATION_RECORDED")  # Event trigger identifier
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIUM")  # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    responsible_role: Mapped[str] = mapped_column(String(50), nullable=False, default="OFFICER")
    verification_status: Mapped[str] = mapped_column(String(30), nullable=False, default="VERIFIED")  # "VERIFIED" | "CONFIGURED" | "REQUIRES_REVIEW" | "INACTIVE"
    source_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
