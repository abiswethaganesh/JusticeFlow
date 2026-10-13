from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict


class ConversationalIntakeRequest(BaseModel):
    complaint_text: str
    conversation_history: Optional[List[dict]] = []
    previous_entities: Optional[dict] = {}


class ConversationalIntakeResponse(BaseModel):
    complaint_type: str
    is_cognizable: bool
    summary: str
    entities: dict
    missing_fields: List[str] = []
    ambiguous_fields: List[str] = []
    follow_up_questions: List[str] = []
    recommended_evidence: List[str] = []
    ai_recommendations: dict = {}


class ComplaintCreateRequest(BaseModel):
    complaint_type: str
    complaint_text: str
    summary: str = ""
    structured_data: dict = {}
    incident_details: dict = {}
    citizen_phone: Optional[str] = ""
    citizen_id: Optional[int] = None
    is_cognizable: bool = True
    priority: str = "MEDIUM"


class ComplaintStatusUpdateRequest(BaseModel):
    status: str
    remarks: Optional[str] = ""


class FIRRegisterRequest(BaseModel):
    iif_data: dict


class FIRRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: str
    fir_number: str
    iif_data: dict
    status: str
    official_cctns_ref_id: Optional[str] = None
    created_at: datetime


class CaseEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: str
    previous_status: Optional[str] = None
    new_status: str
    actor_name: str
    actor_role: str
    remarks: Optional[str] = None
    created_at: datetime


class CaseEvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: str
    evidence_type: str
    title: str
    file_path: str = ""
    file_url: str = ""
    description: Optional[str] = None
    source: Optional[str] = None
    incident_timestamp: Optional[datetime] = None
    identified_at: Optional[datetime] = None
    potentially_time_sensitive: bool = False
    retention_period_days: Optional[int] = None
    retention_source: Optional[str] = None
    retention_confidence: str = "UNKNOWN"
    urgency: str = "UNKNOWN"
    estimated_expiry: Optional[datetime] = None
    preservation_status: str = "NOT_REVIEWED"
    preservation_action_at: Optional[datetime] = None
    preservation_notes: Optional[str] = None
    is_digital_narrative_extracted: bool = False
    uploaded_at: datetime


class PreservationActionRequest(BaseModel):
    action: str
    status: str
    remarks: Optional[str] = ""
    actor_name: Optional[str] = "Officer"
    actor_role: Optional[str] = "OFFICER"


class EvidenceAuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: str
    evidence_id: int
    action: str
    previous_status: Optional[str] = None
    new_status: str
    actor_name: str
    actor_role: str
    time_to_preservation_minutes: Optional[float] = None
    remarks: Optional[str] = None
    created_at: datetime


class EvidenceRetentionRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    evidence_type: str
    display_label: str
    retention_period_days: Optional[int] = None
    source_policy: str
    confidence_level: str
    is_time_sensitive: bool
    default_urgency: str
    preservation_guidelines: Optional[str] = None



class ComplaintRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: str
    citizen_id: Optional[int] = None
    citizen_phone: str = ""
    complaint_type: str
    workflow_type: str
    original_complaint: str
    complaint_text: str
    summary: Optional[str] = ""
    structured_data: dict = {}
    incident_details: dict = {}
    police_station_id: Optional[int] = None
    assigned_station: str = ""
    status: str
    priority: str
    is_cognizable: bool
    created_at: datetime
    updated_at: datetime
