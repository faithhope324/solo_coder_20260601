from typing import Optional
import pandas as pd


TIME_SLOTS = [
    {"key": "breakfast", "name": "早餐", "start": 6, "end": 10, "color": "#FF9F43"},
    {"key": "lunch", "name": "午餐", "start": 11, "end": 14, "color": "#54A0FF"},
    {"key": "afternoon_tea", "name": "下午茶", "start": 14, "end": 17, "color": "#5F27CD"},
    {"key": "dinner", "name": "晚餐", "start": 17, "end": 21, "color": "#10AC84"},
    {"key": "supper", "name": "夜宵", "start": 21, "end": 26, "color": "#EE5253"},
]

SLOT_ORDER = ["breakfast", "lunch", "afternoon_tea", "dinner", "supper"]
SLOT_NAME_MAP = {s["key"]: s["name"] for s in TIME_SLOTS}
SLOT_COLOR_MAP = {s["key"]: s["color"] for s in TIME_SLOTS}


def get_time_slot(hour: int) -> Optional[str]:
    adjusted_hour = hour if hour >= 2 else hour + 24
    for slot in TIME_SLOTS:
        start, end = slot["start"], slot["end"]
        if start <= adjusted_hour < end:
            return slot["key"]
    return None


def get_time_slot_exact(dt) -> Optional[str]:
    hour = dt.hour
    minute = dt.minute
    second = dt.second
    total_seconds = hour * 3600 + minute * 60 + second
    adjusted_seconds = total_seconds if total_seconds >= 2 * 3600 else total_seconds + 24 * 3600
    for slot in TIME_SLOTS:
        start_seconds = slot["start"] * 3600
        end_seconds = slot["end"] * 3600
        if start_seconds <= adjusted_seconds < end_seconds:
            return slot["key"]
    return None


def assign_time_slots(df, hour_col="小时", slot_col="时段"):
    df = df.copy()
    df[slot_col] = df["订单时间"].apply(get_time_slot_exact)
    df[slot_col] = pd.Categorical(df[slot_col], categories=SLOT_ORDER, ordered=True)
    return df


def get_slot_name(slot_key: str) -> str:
    return SLOT_NAME_MAP.get(slot_key, slot_key)


def get_slot_color(slot_key: str) -> str:
    return SLOT_COLOR_MAP.get(slot_key, "#888888")

