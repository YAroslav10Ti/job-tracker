
from fastapi import APIRouter, Depends
from redis.asyncio import Redis

from app.dependencies.auth import get_authenticated_user
from app.dependencies.redis import get_statistics_redis
from app.models import User
from app.services.insights import get_user_insights


router = APIRouter(
    prefix="/insights",
    tags=["Insights"], 
)


@router.get("/")
async def read_insights(
    current_user: User = Depends(get_authenticated_user),
    redis: Redis = Depends(get_statistics_redis),
):
    return await get_user_insights(
        user_id=current_user.id,
        redis=redis,
    )
