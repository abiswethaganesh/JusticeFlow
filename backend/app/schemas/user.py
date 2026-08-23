from typing import Optional
from pydantic import BaseModel, ConfigDict


class CitizenLoginRequest(BaseModel):
    phone: str
    full_name: str
    city: Optional[str] = "Chennai"


class OfficerLoginRequest(BaseModel):
    officer_id: str
    name: str
    station_branch: str
    city: Optional[str] = "Chennai"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    phone: str
    full_name: str
    officer_id: Optional[str] = None
    station_branch: Optional[str] = None
    city: Optional[str] = None
    token: str
