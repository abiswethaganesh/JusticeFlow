from datetime import datetime, timezone

from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Officer(Base):
    __tablename__ = "officers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    officer_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    badge_number: Mapped[str] = mapped_column(String(50), nullable=True)
    rank: Mapped[str] = mapped_column(String(50), nullable=False, default="Inspector")
    police_station_id: Mapped[int] = mapped_column(Integer, ForeignKey("police_stations.id"), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
