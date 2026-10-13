from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class LegalProcedureRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rule_code: str
    title: str
    legal_source: str
    section_reference: str
    description: str
    applicability_conditions: dict = {}
    deadline_value: Optional[int] = None
    deadline_unit: str
    start_event: str
    severity: str
    responsible_role: str
    verification_status: str
    source_url: Optional[str] = None
    is_active: bool


class CaseObligationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: str
    rule_id: int
    start_date: datetime
    due_date: Optional[datetime] = None
    status: str
    responsible_role: str
    responsible_user_id: Optional[int] = None
    completion_at: Optional[datetime] = None
    completion_notes: Optional[str] = None
    reminder_sent_at: Optional[datetime] = None
    escalation_status: str
    applicability_reason: str
    review_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    rule: Optional[LegalProcedureRuleResponse] = None
    days_remaining: Optional[int] = None
    days_overdue: Optional[int] = None


class ObligationAuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    obligation_id: int
    case_id: str
    action: str
    previous_status: Optional[str] = None
    new_status: str
    actor_id: Optional[int] = None
    actor_name: str
    actor_role: str
    remarks: Optional[str] = None
    timestamp: datetime


class ObligationActionRequest(BaseModel):
    completion_notes: Optional[str] = None
    reason: Optional[str] = None
    actor_name: Optional[str] = "Officer"
    actor_role: Optional[str] = "OFFICER"
