from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ShortLink(Base):
    __tablename__ = "short_links"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    short_code: Mapped[str] = mapped_column(String(10), unique=True, index=True, nullable=False)
    original_url: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    daily_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    total_clicks: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
