from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ComplaintCreateRequest(BaseModel):
    complaint_type: str
    complaint_text: str
    summary: str = ""
    structured_data: dict = {}
    citizen_phone: Optional[str] = ""
    assigned_station: Optional[str] = ""


class ComplaintStatusUpdateRequest(BaseModel):
    status: str


class ComplaintRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: str
    complaint_type: str
    complaint_text: str
    summary: str
    structured_data: dict
    status: str
    citizen_phone: str = ""
    assigned_station: str = ""
    created_at: datetime
