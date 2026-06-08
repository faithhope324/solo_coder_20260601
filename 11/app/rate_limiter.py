from app.inventory import get_redis


async def check_rate_limit(user_id: int, product_id: int) -> bool:
    r = await get_redis()
    key = f"rate:{user_id}:{product_id}"
    current = await r.incr(key)
    if current == 1:
        await r.expire(key, 1)
    return current <= 1
