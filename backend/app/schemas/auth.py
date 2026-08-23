from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr


class CitizenRegisterRequest(BaseModel):
    email: str
    phone: str
    full_name: str
    password: str
    city: Optional[str] = "Chennai"


class LoginRequest(BaseModel):
    login_identifier: str  # email, phone, or officer_id
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    email: str
    phone: str
    full_name: str
    officer_id: Optional[str] = None
    station_branch: Optional[str] = None
    city: Optional[str] = None
    access_token: str
    token_type: str = "bearer"
