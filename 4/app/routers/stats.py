from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.stat import AccessLogOut, LinkStatsSummary
from app.services import link_service, stat_service

router = APIRouter(prefix="/api/stats", tags=["Statistics"])


@router.get("/{short_code}", response_model=LinkStatsSummary)
async def get_link_stats(
    short_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    link = link_service.get_link_by_code(db, short_code)
    if not link or link.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Link not found")
    return stat_service.get_link_stats_summary(db, short_code)


@router.get("/{short_code}/logs", response_model=list[AccessLogOut])
async def get_access_logs(
    short_code: str,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    link = link_service.get_link_by_code(db, short_code)
    if not link or link.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Link not found")
    return stat_service.get_access_logs(db, short_code, skip, limit)
