from typing import Optional
from pydantic import BaseModel


class MissingFieldsRequest(BaseModel):
    complaint_type: str
    entities: dict = {}


class MissingFieldsResponse(BaseModel):
    form_id: Optional[str] = None
    required_fields: list[str] = []
    missing_fields: list[str] = []
