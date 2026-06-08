from datetime import datetime

from pydantic import BaseModel


class AccessLogOut(BaseModel):
    id: int
    short_code: str
    ip_address: str
    device_type: str
    browser: str | None = None
    os: str | None = None
    referer: str | None = None
    accessed_at: datetime

    model_config = {"from_attributes": True}


class DailyStats(BaseModel):
    date: str
    count: int


class DeviceStats(BaseModel):
    device_type: str
    count: int


class LinkStatsSummary(BaseModel):
    short_code: str
    total_clicks: int
    today_clicks: int
    unique_ips: int
    device_breakdown: list[DeviceStats]
    daily_trend: list[DailyStats]
