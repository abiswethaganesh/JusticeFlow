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
    file_path: str
    file_url: str
    description: Optional[str] = None
    uploaded_at: datetime


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
