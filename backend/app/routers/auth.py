from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.officer import Officer
from app.schemas.auth import CitizenRegisterRequest, LoginRequest, UserResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def get_current_user_from_token(
    db: Session = Depends(get_db),
    authorization: str = Header(None),
    x_user_role: str = Header(None, alias="X-User-Role"),
    x_user_phone: str = Header(None, alias="X-User-Phone"),
    x_user_id: str = Header(None, alias="X-User-Id"),
) -> Optional[User]:
    """Dependency to extract authenticated user from Bearer JWT or legacy auth headers."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            payload = auth_service.decode_access_token(token)
            if payload and "user_id" in payload:
                user = db.query(User).filter(User.id == payload["user_id"]).first()
                if user:
                    return user
        except Exception:
            pass

    if x_user_id and str(x_user_id).isdigit():
        user = db.query(User).filter(User.id == int(x_user_id)).first()
        if user:
            return user

    if x_user_phone:
        user = db.query(User).filter((User.phone == x_user_phone) | (User.officer_id == x_user_phone)).first()
        if user:
            return user

    return None


@router.post("/register", response_model=UserResponse)
def register_citizen(payload: CitizenRegisterRequest, db: Session = Depends(get_db)):
    if not payload.email or "@" not in payload.email:
        raise HTTPException(status_code=400, detail="Valid email address is required.")
    if not payload.password or len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    user = auth_service.register_citizen(
        db,
        email=payload.email,
        phone=payload.phone,
        full_name=payload.full_name,
        password=payload.password,
        city=payload.city or "Chennai",
    )

    token = auth_service.create_access_token({"sub": user.email, "user_id": user.id, "role": user.role})
    return UserResponse(
        id=user.id,
        role=user.role,
        email=user.email,
        phone=user.phone,
        full_name=user.full_name,
        city=user.city,
        access_token=token,
    )


@router.post("/login", response_model=UserResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    auth_service.seed_default_users_if_needed(db)

    user = auth_service.authenticate_user(db, payload.login_identifier, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials. Check your email/phone/officer ID and password.")

    token_data = {"sub": user.email, "user_id": user.id, "role": user.role}

    if user.role == "OFFICER":
        officer = db.query(Officer).filter(Officer.user_id == user.id).first()
        if officer:
            token_data["police_station_id"] = officer.police_station_id

    token = auth_service.create_access_token(token_data)

    return UserResponse(
        id=user.id,
        role=user.role,
        email=user.email,
        phone=user.phone,
        full_name=user.full_name,
        officer_id=user.officer_id,
        station_branch=user.station_branch,
        city=user.city,
        access_token=token,
    )


@router.post("/citizen/login", response_model=UserResponse)
def citizen_login_legacy(payload: dict, db: Session = Depends(get_db)):
    """Convenience endpoint for citizen quick login/register."""
    auth_service.seed_default_users_if_needed(db)
    phone = payload.get("phone", "9876543210")
    name = payload.get("full_name") or payload.get("name") or "Rahul Kumar"
    email = payload.get("email") or f"citizen_{phone}@justiceflow.org"
    password = payload.get("password") or "Citizen123!"

    user = db.query(User).filter((User.phone == phone) | (User.email == email)).first()
    if not user:
        user = auth_service.register_citizen(db, email, phone, name, password, payload.get("city", "Chennai"))

    token = auth_service.create_access_token({"sub": user.email, "user_id": user.id, "role": user.role})
    return UserResponse(
        id=user.id,
        role=user.role,
        email=user.email,
        phone=user.phone,
        full_name=user.full_name,
        city=user.city,
        access_token=token,
    )


@router.post("/officer/login", response_model=UserResponse)
def officer_login_legacy(payload: dict, db: Session = Depends(get_db)):
    """Convenience endpoint for officer quick login."""
    auth_service.seed_default_users_if_needed(db)
    officer_id = payload.get("officer_id") or "OFF-101"
    password = payload.get("password") or "Officer123!"

    user = auth_service.authenticate_user(db, officer_id, password)
    if not user:
        user = db.query(User).filter(User.officer_id == officer_id).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid Officer ID or Password.")

    officer = db.query(Officer).filter(Officer.user_id == user.id).first()
    st_id = officer.police_station_id if officer else 1

    token = auth_service.create_access_token(
        {"sub": user.email, "user_id": user.id, "role": "OFFICER", "police_station_id": st_id}
    )

    return UserResponse(
        id=user.id,
        role=user.role,
        email=user.email,
        phone=user.phone,
        full_name=user.full_name,
        officer_id=user.officer_id,
        station_branch=user.station_branch,
        city=user.city,
        access_token=token,
    )


@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user_from_token)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    token = auth_service.create_access_token({"sub": user.email, "user_id": user.id, "role": user.role})
    return UserResponse(
        id=user.id,
        role=user.role,
        email=user.email,
        phone=user.phone,
        full_name=user.full_name,
        officer_id=user.officer_id,
        station_branch=user.station_branch,
        city=user.city,
        access_token=token,
    )
