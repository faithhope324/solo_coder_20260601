from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models.short_link import ShortLink
from app.models.user import User
from app.schemas.short_link import ShortLinkCreate, ShortLinkUpdate, ShortLinkOut, ShortLinkAccess
from app.services import link_service, cache_service, stat_service

router = APIRouter(prefix="/api/links", tags=["Short Links"])


def _link_to_out(link: ShortLink) -> ShortLinkOut:
    out = ShortLinkOut.model_validate(link)
    out.short_url = f"{settings.BASE_URL}/s/{link.short_code}"
    out.has_password = link.password is not None
    return out


@router.post("/", response_model=ShortLinkOut, status_code=status.HTTP_201_CREATED)
async def create_link(
    data: ShortLinkCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        link = link_service.create_short_link(db, current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _link_to_out(link)


@router.get("/", response_model=list[ShortLinkOut])
async def list_my_links(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    links = link_service.get_links_by_user(db, current_user.id, skip, limit)
    return [_link_to_out(link) for link in links]


@router.get("/{short_code}", response_model=ShortLinkOut)
async def get_link_detail(
    short_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    link = link_service.get_link_by_code(db, short_code)
    if not link or link.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Link not found")
    return _link_to_out(link)


@router.put("/{short_code}", response_model=ShortLinkOut)
async def update_link(
    short_code: str,
    data: ShortLinkUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    link = link_service.get_link_by_code(db, short_code)
    if not link or link.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Link not found")
    link = link_service.update_short_link(db, link, data)
    await cache_service.invalidate_cached_link(short_code)
    return _link_to_out(link)


@router.delete("/{short_code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link(
    short_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    link = link_service.get_link_by_code(db, short_code)
    if not link or link.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Link not found")
    db.delete(link)
    db.commit()
    await cache_service.invalidate_cached_link(short_code)


@router.get("/s/{short_code}")
async def redirect_short_link(
    short_code: str,
    request: Request,
    db: Session = Depends(get_db),
):
    cached_url = await cache_service.get_cached_link(short_code)
    if cached_url:
        link = link_service.get_link_by_code(db, short_code)
        if not link or not link.is_active:
            raise HTTPException(status_code=404, detail="Link not found")
    else:
        link = link_service.get_link_by_code(db, short_code)
        if not link or not link.is_active:
            raise HTTPException(status_code=404, detail="Link not found")
        if link_service.is_link_expired(link):
            raise HTTPException(status_code=410, detail="Link has expired")

    if link_service.is_link_expired(link):
        raise HTTPException(status_code=410, detail="Link has expired")

    if link.daily_limit is not None:
        daily_count = await cache_service.get_daily_access_count(short_code)
        if daily_count < 0:
            daily_count = link_service.get_today_click_count(db, short_code)
        if daily_count >= link.daily_limit:
            raise HTTPException(status_code=429, detail="Daily access limit reached")

    if link.password:
        client_ip = request.client.host if request.client else "unknown"
        pwd_verified = await cache_service.is_password_verified(short_code, client_ip)
        if not pwd_verified:
            raise HTTPException(
                status_code=403,
                detail="Password required. POST to /api/links/s/{short_code}/verify with password.",
            )

    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    referer = request.headers.get("referer")

    await stat_service.record_access(db, short_code, ip_address, user_agent, referer)
    link_service.increment_clicks(db, link)

    is_hot = await cache_service.is_hot_link(short_code)
    if is_hot and not cached_url:
        await cache_service.set_cached_link(short_code, link.original_url)

    return Response(status_code=302, headers={"Location": link.original_url})


@router.post("/s/{short_code}/verify")
async def verify_link_password(
    short_code: str,
    data: ShortLinkAccess,
    request: Request,
    db: Session = Depends(get_db),
):
    link = link_service.get_link_by_code(db, short_code)
    if not link or not link.is_active:
        raise HTTPException(status_code=404, detail="Link not found")

    if not link.password:
        return {"detail": "No password required", "redirect": f"/api/links/s/{short_code}"}

    if not data.password or data.password != link.password:
        raise HTTPException(status_code=403, detail="Incorrect password")

    client_ip = request.client.host if request.client else "unknown"
    await cache_service.cache_password_verify(short_code, client_ip)

    return {"detail": "Password verified", "redirect": f"/api/links/s/{short_code}"}
