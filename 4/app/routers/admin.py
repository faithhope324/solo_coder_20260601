from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_admin_user
from app.models.short_link import ShortLink
from app.models.user import User
from app.schemas.short_link import ShortLinkOut
from app.schemas.stat import LinkStatsSummary
from app.schemas.user import UserOut
from app.services import link_service, stat_service, auth_service

router = APIRouter(prefix="/api/admin", tags=["Admin"])


def _link_to_out(link: ShortLink) -> ShortLinkOut:
    out = ShortLinkOut.model_validate(link)
    out.short_url = f"{settings.BASE_URL}/s/{link.short_code}"
    out.has_password = link.password is not None
    return out


@router.get("/links", response_model=list[ShortLinkOut])
async def admin_list_links(
    skip: int = 0,
    limit: int = 50,
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    links = link_service.get_all_links(db, skip, limit)
    return [_link_to_out(link) for link in links]


@router.get("/links/count")
async def admin_link_count(
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    return {"total_links": link_service.count_all_links(db)}


@router.get("/links/{short_code}/stats", response_model=LinkStatsSummary)
async def admin_link_stats(
    short_code: str,
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    link = link_service.get_link_by_code(db, short_code)
    if not link:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Link not found")
    return stat_service.get_link_stats_summary(db, short_code)


@router.get("/users", response_model=list[UserOut])
async def admin_list_users(
    skip: int = 0,
    limit: int = 50,
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.get("/overview")
async def admin_overview(
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    total_links = link_service.count_all_links(db)
    total_clicks = stat_service.get_total_clicks(db)
    total_users = db.query(User).count()
    return {
        "total_links": total_links,
        "total_clicks": total_clicks,
        "total_users": total_users,
    }
