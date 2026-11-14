import json

from redis.asyncio import Redis
from datetime import datetime


async def add_user_history(
    redis: Redis,
    user_id: int,
    action: str,
    details: dict
):
    history_key = f"user:{user_id}:history"

    event = json.dumps({
        "action": action,
        "details": details,
        "timestamp": datetime.now().isoformat()
    })

    async with redis.pipeline() as pipe:
        pipe.rpush(history_key, event)
        pipe.ltrim(history_key, -10, -1)
        pipe.expire(history_key, 60 * 60 * 24 * 30)

        await pipe.execute()



async def get_user_history(redis: Redis, user_id: int):
    history_key = f"user:{user_id}:history"

    history = await redis.lrange(history_key, 0, -1)

    return [json.loads(item) for item in history]