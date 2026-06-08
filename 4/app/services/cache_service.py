import asyncio
import datetime
from typing import Any

from app.config import settings

try:
    import redis.asyncio as redis
    _REDIS_AVAILABLE = True
except ImportError:
    redis = None
    _REDIS_AVAILABLE = False

redis_client: Any = None
_memory_cache: dict[str, Any] = {}
_memory_ttl: dict[str, tuple[Any, float]] = {}
_use_memory_fallback: bool = True

CACHE_PREFIX = "shortlink:"
CACHE_HOT_PREFIX = "hot:"
CACHE_TTL = 3600
CACHE_HIT_THRESHOLD = 100


def _now() -> float:
    return datetime.datetime.now(datetime.timezone.utc).timestamp()


def _cleanup_expired() -> None:
    now = _now()
    expired_keys = [k for k, (_, ttl) in _memory_ttl.items() if ttl <= now]
    for k in expired_keys:
        del _memory_ttl[k]
        if k in _memory_cache:
            del _memory_cache[k]


async def init_redis() -> Any:
    global redis_client, _use_memory_fallback

    if not settings.USE_REDIS or not _REDIS_AVAILABLE:
        _use_memory_fallback = True
        print("[Cache] Using in-memory cache (fallback mode)")
        return None

    try:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True, socket_timeout=2)
        await redis_client.ping()
        _use_memory_fallback = False
        print("[Cache] Redis connected successfully")
        return redis_client
    except Exception as e:
        _use_memory_fallback = True
        redis_client = None
        print(f"[Cache] Redis connection failed: {e}. Using in-memory cache (fallback mode)")
        return None


async def close_redis() -> None:
    global redis_client
    if redis_client and not _use_memory_fallback:
        try:
            await redis_client.close()
        except Exception:
            pass
    redis_client = None


async def get_cached_link(short_code: str) -> str | None:
    key = f"{CACHE_PREFIX}{short_code}"

    if _use_memory_fallback:
        _cleanup_expired()
        if key in _memory_ttl and _memory_ttl[key][1] > _now():
            return str(_memory_cache.get(key))
        return None

    if not redis_client:
        return None
    try:
        return await redis_client.get(key)
    except Exception:
        return None


async def set_cached_link(short_code: str, original_url: str, ttl: int = CACHE_TTL) -> None:
    key = f"{CACHE_PREFIX}{short_code}"

    if _use_memory_fallback:
        _memory_cache[key] = original_url
        _memory_ttl[key] = (original_url, _now() + ttl)
        _cleanup_expired()
        return

    if not redis_client:
        return
    try:
        await redis_client.set(key, original_url, ex=ttl)
    except Exception:
        pass


async def invalidate_cached_link(short_code: str) -> None:
    key = f"{CACHE_PREFIX}{short_code}"

    if _use_memory_fallback:
        _memory_cache.pop(key, None)
        _memory_ttl.pop(key, None)
        return

    if not redis_client:
        return
    try:
        await redis_client.delete(key)
    except Exception:
        pass


async def increment_link_hits(short_code: str) -> int:
    key = f"{CACHE_HOT_PREFIX}{short_code}"

    if _use_memory_fallback:
        current = int(_memory_cache.get(key, 0)) + 1
        _memory_cache[key] = current
        if key not in _memory_ttl or _memory_ttl[key][1] <= _now():
            _memory_ttl[key] = (current, _now() + 86400)
        _cleanup_expired()
        return current

    if not redis_client:
        return 0
    try:
        hits = await redis_client.incr(key)
        if hits == 1:
            await redis_client.expire(key, 86400)
        return hits
    except Exception:
        return 0


async def is_hot_link(short_code: str) -> bool:
    key = f"{CACHE_HOT_PREFIX}{short_code}"

    if _use_memory_fallback:
        _cleanup_expired()
        hits = _memory_cache.get(key, 0)
        return int(hits) >= CACHE_HIT_THRESHOLD

    if not redis_client:
        return False
    try:
        hits = await redis_client.get(key)
        return hits is not None and int(hits) >= CACHE_HIT_THRESHOLD
    except Exception:
        return False


async def get_daily_access_count(short_code: str) -> int:
    key = f"daily:{short_code}"

    if _use_memory_fallback:
        _cleanup_expired()
        return int(_memory_cache.get(key, 0))

    if not redis_client:
        return -1
    try:
        count = await redis_client.get(key)
        return int(count) if count is not None else 0
    except Exception:
        return -1


async def increment_daily_access(short_code: str) -> int:
    key = f"daily:{short_code}"

    if _use_memory_fallback:
        current = int(_memory_cache.get(key, 0)) + 1
        _memory_cache[key] = current
        if key not in _memory_ttl or _memory_ttl[key][1] <= _now():
            import datetime
            tomorrow = datetime.datetime.now(datetime.timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            ) + datetime.timedelta(days=1)
            seconds_until_midnight = int((tomorrow - datetime.datetime.now(datetime.timezone.utc)).total_seconds())
            _memory_ttl[key] = (current, _now() + max(seconds_until_midnight, 1))
        _cleanup_expired()
        return current

    if not redis_client:
        return -1
    try:
        count = await redis_client.incr(key)
        if count == 1:
            import datetime
            tomorrow = datetime.datetime.now(datetime.timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            ) + datetime.timedelta(days=1)
            seconds_until_midnight = int((tomorrow - datetime.datetime.now(datetime.timezone.utc)).total_seconds())
            await redis_client.expire(key, max(seconds_until_midnight, 1))
        return count
    except Exception:
        return -1


async def cache_password_verify(short_code: str, ip_address: str, ttl: int = 1800) -> None:
    key = f"pwd_verified:{short_code}:{ip_address}"

    if _use_memory_fallback:
        _memory_cache[key] = "1"
        _memory_ttl[key] = ("1", _now() + ttl)
        _cleanup_expired()
        return

    if not redis_client:
        return
    try:
        await redis_client.set(key, "1", ex=ttl)
    except Exception:
        pass


async def is_password_verified(short_code: str, ip_address: str) -> bool:
    key = f"pwd_verified:{short_code}:{ip_address}"

    if _use_memory_fallback:
        _cleanup_expired()
        return key in _memory_cache and _memory_ttl.get(key, (None, 0))[1] > _now()

    if not redis_client:
        return False
    try:
        return await redis_client.exists(key) > 0
    except Exception:
        return False
