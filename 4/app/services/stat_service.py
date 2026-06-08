from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.models.stat import AccessLog
from app.schemas.stat import AccessLogOut, DailyStats, DeviceStats, LinkStatsSummary
from app.services import cache_service

_sqlite = settings.DATABASE_URL.startswith("sqlite")


def parse_device_type(user_agent_str: str) -> dict:
    try:
        from user_agents import parse
    except ImportError:
        return {"device_type": "Unknown", "browser": "Unknown", "os": "Unknown"}

    ua = parse(user_agent_str)
    if ua.is_mobile:
        device_type = "Mobile"
    elif ua.is_tablet:
        device_type = "Tablet"
    elif ua.is_pc:
        device_type = "Desktop"
    elif ua.is_bot:
        device_type = "Bot"
    else:
        device_type = "Unknown"

    return {
        "device_type": device_type,
        "browser": ua.browser.family or "Unknown",
        "os": ua.os.family or "Unknown",
    }


async def record_access(
    db: Session,
    short_code: str,
    ip_address: str,
    user_agent: str,
    referer: str | None = None,
) -> None:
    device_info = parse_device_type(user_agent)
    log = AccessLog(
        short_code=short_code,
        ip_address=ip_address,
        device_type=device_info["device_type"],
        browser=device_info["browser"],
        os=device_info["os"],
        user_agent=user_agent,
        referer=referer,
    )
    db.add(log)
    db.commit()
    await cache_service.increment_daily_access(short_code)
    await cache_service.increment_link_hits(short_code)


def get_access_logs(
    db: Session, short_code: str, skip: int = 0, limit: int = 50
) -> list[AccessLog]:
    return (
        db.query(AccessLog)
        .filter(AccessLog.short_code == short_code)
        .order_by(AccessLog.accessed_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_link_stats_summary(db: Session, short_code: str) -> LinkStatsSummary:
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    total_clicks = (
        db.query(func.count(AccessLog.id))
        .filter(AccessLog.short_code == short_code)
        .scalar() or 0
    )

    today_clicks = (
        db.query(func.count(AccessLog.id))
        .filter(AccessLog.short_code == short_code, AccessLog.accessed_at >= today_start)
        .scalar() or 0
    )

    unique_ips = (
        db.query(func.count(func.distinct(AccessLog.ip_address)))
        .filter(AccessLog.short_code == short_code)
        .scalar() or 0
    )

    device_rows = (
        db.query(AccessLog.device_type, func.count(AccessLog.id).label("count"))
        .filter(AccessLog.short_code == short_code)
        .group_by(AccessLog.device_type)
        .all()
    )
    device_breakdown = [DeviceStats(device_type=r[0], count=r[1]) for r in device_rows]

    if _sqlite:
        date_col = func.date(AccessLog.accessed_at).label("date")
    else:
        from sqlalchemy import cast, Date
        date_col = cast(AccessLog.accessed_at, Date).label("date")

    daily_rows = (
        db.query(
            date_col,
            func.count(AccessLog.id).label("count"),
        )
        .filter(AccessLog.short_code == short_code)
        .group_by(date_col)
        .order_by(date_col.desc())
        .limit(30)
        .all()
    )
    daily_trend = [DailyStats(date=str(r[0]), count=r[1]) for r in daily_rows]

    return LinkStatsSummary(
        short_code=short_code,
        total_clicks=total_clicks,
        today_clicks=today_clicks,
        unique_ips=unique_ips,
        device_breakdown=device_breakdown,
        daily_trend=daily_trend,
    )


def get_total_clicks(db: Session) -> int:
    return db.query(func.count(AccessLog.id)).scalar() or 0
