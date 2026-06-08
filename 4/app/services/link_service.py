import random
import string

from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.short_link import ShortLink
from app.models.stat import AccessLog
from app.schemas.short_link import ShortLinkCreate, ShortLinkUpdate


def generate_short_code(length: int = 6) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))


def generate_unique_code(db: Session, length: int = 6, max_attempts: int = 10) -> str:
    for _ in range(max_attempts):
        code = generate_short_code(length)
        if not db.query(ShortLink).filter(ShortLink.short_code == code).first():
            return code
    return generate_unique_code(db, length + 1)


def create_short_link(db: Session, user_id: int, data: ShortLinkCreate) -> ShortLink:
    if data.custom_code:
        existing = db.query(ShortLink).filter(ShortLink.short_code == data.custom_code).first()
        if existing:
            raise ValueError("Custom code already exists")
        code = data.custom_code
    else:
        code = generate_unique_code(db)

    link = ShortLink(
        short_code=code,
        original_url=data.original_url,
        user_id=user_id,
        password=data.password,
        daily_limit=data.daily_limit,
        expires_at=data.expires_at,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


def update_short_link(db: Session, link: ShortLink, data: ShortLinkUpdate) -> ShortLink:
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(link, key, value)
    db.commit()
    db.refresh(link)
    return link


def get_link_by_code(db: Session, short_code: str) -> ShortLink | None:
    return db.query(ShortLink).filter(ShortLink.short_code == short_code).first()


def get_links_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 20) -> list[ShortLink]:
    return (
        db.query(ShortLink)
        .filter(ShortLink.user_id == user_id)
        .order_by(ShortLink.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_all_links(db: Session, skip: int = 0, limit: int = 50) -> list[ShortLink]:
    return (
        db.query(ShortLink)
        .order_by(ShortLink.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def count_links_by_user(db: Session, user_id: int) -> int:
    return db.query(ShortLink).filter(ShortLink.user_id == user_id).count()


def count_all_links(db: Session) -> int:
    return db.query(ShortLink).count()


def is_link_expired(link: ShortLink) -> bool:
    if link.expires_at is None:
        return False
    return datetime.now(timezone.utc) > link.expires_at.replace(tzinfo=timezone.utc)


def get_today_click_count(db: Session, short_code: str) -> int:
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return (
        db.query(func.count(AccessLog.id))
        .filter(AccessLog.short_code == short_code, AccessLog.accessed_at >= today_start)
        .scalar()
    )


def increment_clicks(db: Session, link: ShortLink) -> None:
    link.total_clicks += 1
    db.commit()
