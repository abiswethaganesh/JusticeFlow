"""
Authentication and JWT token service for Citizens and Officers.
Supports password hashing, JWT generation & decoding, user registration, and database seeding.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.models.officer import Officer
from app.models.police_station import PoliceStation
from app.services.jurisdiction_service import seed_police_stations_if_needed

# Password hashing context using bcrypt with pbkdf2_sha256 fallback
pwd_context = CryptContext(schemes=["bcrypt", "pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except jwt.PyJWTError:
        return None


def register_citizen(db: Session, email: str, phone: str, full_name: str, password: str, city: str = "Chennai") -> User:
    existing = db.query(User).filter((User.email == email) | (User.phone == phone)).first()
    if existing:
        return existing

    user = User(
        role="CITIZEN",
        email=email.lower().strip(),
        phone=phone.strip(),
        password_hash=hash_password(password),
        full_name=full_name.strip(),
        city=city,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, login_identifier: str, password: str) -> Optional[User]:
    identifier = login_identifier.strip()
    user = (
        db.query(User)
        .filter((User.email == identifier.lower()) | (User.phone == identifier) | (User.officer_id == identifier))
        .first()
    )
    if not user:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


def seed_default_users_if_needed(db: Session):
    """Pre-seeds default police stations and test officer accounts if not present."""
    seed_police_stations_if_needed(db)

    # Check if test officer exists
    off_user = db.query(User).filter(User.officer_id == "OFF-101").first()
    if not off_user:
        # Fetch Anna Nagar PS
        st1 = db.query(PoliceStation).filter(PoliceStation.station_code == "AN-PS-01").first()
        if st1:
            user1 = User(
                role="OFFICER",
                email="officer101@police.gov.in",
                phone="9999000101",
                password_hash=hash_password("Officer123!"),
                full_name="Inspector Rajesh Kumar",
                officer_id="OFF-101",
                station_branch=st1.station_name,
                city="Chennai",
            )
            db.add(user1)
            db.flush()

            officer1 = Officer(
                user_id=user1.id,
                officer_id="OFF-101",
                badge_number="TN-POL-101",
                rank="Inspector",
                police_station_id=st1.id,
            )
            db.add(officer1)

        # Fetch T. Nagar PS
        st2 = db.query(PoliceStation).filter(PoliceStation.station_code == "TN-PS-02").first()
        if st2:
            user2 = User(
                role="OFFICER",
                email="officer102@police.gov.in",
                phone="9999000102",
                password_hash=hash_password("Officer123!"),
                full_name="Inspector Priya Sharma",
                officer_id="OFF-102",
                station_branch=st2.station_name,
                city="Chennai",
            )
            db.add(user2)
            db.flush()

            officer2 = Officer(
                user_id=user2.id,
                officer_id="OFF-102",
                badge_number="TN-POL-102",
                rank="Inspector",
                police_station_id=st2.id,
            )
            db.add(officer2)

        # Create demo citizen account
        cit_user = db.query(User).filter(User.email == "citizen@justiceflow.org").first()
        if not cit_user:
            citizen = User(
                role="CITIZEN",
                email="citizen@justiceflow.org",
                phone="9876543210",
                password_hash=hash_password("Citizen123!"),
                full_name="Rahul Kumar",
                city="Chennai",
            )
            db.add(citizen)

        db.commit()
