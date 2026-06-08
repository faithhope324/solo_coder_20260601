from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AccessLog(Base):
    __tablename__ = "access_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    short_code: Mapped[str] = mapped_column(String(10), ForeignKey("short_links.short_code"), index=True, nullable=False)
    ip_address: Mapped[str] = mapped_column(String(50), nullable=False)
    device_type: Mapped[str] = mapped_column(String(20), nullable=False)
    browser: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    os: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    referer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    accessed_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
