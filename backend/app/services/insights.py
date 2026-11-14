from redis.asyncio import Redis


async def get_user_insights(
    user_id: int,
    redis: Redis,
) -> dict:
    key = f"user:{user_id}:job_insights"

    stats = await redis.hgetall(key)

    total = int(stats.get("total", 0))
    interview = int(stats.get("interview", 0))
    rejected = int(stats.get("rejected", 0))

    interview_rate = (
        round(interview / total * 100, 2)
        if total > 0 else 0.0
    )

    rejection_rate = (
        round(rejected / total * 100, 2)
        if total > 0 else 0.0
    )

    return {
        "total": total,
        "interview": interview,
        "rejected": rejected,
        "interview_rate": interview_rate,
        "rejection_rate": rejection_rate,
    }    