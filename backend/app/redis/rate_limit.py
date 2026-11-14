from redis.asyncio import Redis


async def check_rate_limit(
    redis: Redis,
    key: str,
    limit: int,
    window: int
) -> bool:

    current = await redis.incr(key)

    if current == 1:
        await redis.expire(key, window)

    return current <= limit