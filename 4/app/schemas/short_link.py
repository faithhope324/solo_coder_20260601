from datetime import datetime

from pydantic import BaseModel, HttpUrl


class ShortLinkCreate(BaseModel):
    original_url: str
    custom_code: str | None = None
    password: str | None = None
    daily_limit: int | None = None
    expires_at: datetime | None = None


class ShortLinkUpdate(BaseModel):
    original_url: str | None = None
    password: str | None = None
    daily_limit: int | None = None
    expires_at: datetime | None = None
    is_active: bool | None = None


class ShortLinkOut(BaseModel):
    id: int
    short_code: str
    original_url: str
    short_url: str = ""
    has_password: bool = False
    daily_limit: int | None = None
    expires_at: datetime | None = None
    is_active: bool
    total_clicks: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ShortLinkAccess(BaseModel):
    password: str | None = None
