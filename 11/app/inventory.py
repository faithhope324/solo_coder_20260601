from app.config import USE_FAKEREDIS

redis_client = None


async def get_redis():
    global redis_client
    if redis_client is None:
        if USE_FAKEREDIS == "1":
            import fakeredis.aioredis
            redis_client = fakeredis.aioredis.FakeRedis(decode_responses=True)
        else:
            import redis.asyncio as aioredis
            from app.config import REDIS_URL
            redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
    return redis_client


async def close_redis():
    global redis_client
    if redis_client is not None:
        if hasattr(redis_client, "close"):
            await redis_client.close()
        redis_client = None


async def init_stock_cache(product_id: int, total_stock: int):
    r = await get_redis()
    key = f"stock:{product_id}"
    exists = await r.exists(key)
    if not exists:
        await r.set(key, total_stock)


async def decr_stock(product_id: int) -> int:
    r = await get_redis()
    key = f"stock:{product_id}"
    remaining = await r.decr(key)
    return remaining


async def incr_stock(product_id: int) -> int:
    r = await get_redis()
    key = f"stock:{product_id}"
    return await r.incr(key)


async def get_stock(product_id: int) -> int:
    r = await get_redis()
    key = f"stock:{product_id}"
    val = await r.get(key)
    return int(val) if val is not None else 0
