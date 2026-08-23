from datetime import datetime, timezone

from sqlalchemy import Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PoliceStation(Base):
    __tablename__ = "police_stations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    station_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    jurisdiction_area: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # {"keywords": [...], "pincodes": [...]}
    city: Mapped[str] = mapped_column(String(50), nullable=False, default="Chennai")
    address: Mapped[str] = mapped_column(Text, nullable=True)
    contact_number: Mapped[str] = mapped_column(String(30), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
