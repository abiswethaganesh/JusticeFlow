from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Integer, String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # "CITIZEN" | "OFFICER"
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Officer-specific fields
    officer_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    station_branch: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
