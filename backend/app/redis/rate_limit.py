from redis.asyncio import Redis


async def check_rate_limit(redis: Redis, key: str, limit: int, window: int) -> bool:
    # INCR и EXPIRE NX в одной транзакции: ключ всегда получает TTL
    async with redis.pipeline(transaction=True) as pipe:
        pipe.incr(key)
        pipe.expire(key, window, nx=True)
        current, _ = await pipe.execute()
    return current <= limit
