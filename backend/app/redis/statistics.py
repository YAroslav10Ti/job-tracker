
import json

from redis import Redis as SyncRedis
from redis.asyncio import Redis as AsyncRedis


def save_job_statistics(
    redis: SyncRedis,
    user_id: int,
    statistics: dict[str, int],
) -> None:
    key = f"jobs:statistics:user:{user_id}"

    redis.set(
        key,
        json.dumps(statistics, ensure_ascii=False),
        ex=300,
    )


async def get_job_statistics( 
    redis: AsyncRedis,
    user_id: int,
) -> dict[str, int] | None:
    key = f"jobs:statistics:user:{user_id}"

    cached_statistics = await redis.get(key)

    if cached_statistics is None:
        return None

    return json.loads(cached_statistics)


async def acquire_statistics_lock(
    redis: AsyncRedis,
    user_id: int,
) -> bool:
    lock_key = f"jobs:statistics:lock:user:{user_id}"

    result = await redis.set(
        lock_key,
        "1",
        nx=True,
        ex=60,
    )

    return bool(result)
