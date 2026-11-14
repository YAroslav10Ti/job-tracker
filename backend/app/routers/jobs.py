from fastapi import status, APIRouter
from app.schemas import JobCreate, JobResponse, JobUpdate, UserCreateLogin, UserResponse, UserLoginResponse
from app.database import get_db
from fastapi import Depends
from app.services.jobs import (
    create_job_service,
    get_jobs_service,
    get_job_service,
    update_job_service,
    delete_job_service,
    create_user, 
    login_new_user, 
    change_password_services, 
    delete_user_services,
    get_user_history_services
)
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Job
from app.dependencies.auth import get_authenticated_user
from app.dependencies.redis import get_redis
from redis.asyncio import Redis

import logging 
from app.dependencies.redis import get_statistics_redis
from app.redis.statistics import acquire_statistics_lock
from app.tasks import calculate_job_statistics
from app.redis.statistics import get_job_statistics
from fastapi import APIRouter, Depends
from redis.asyncio import Redis

from app.dependencies.auth import get_authenticated_user


logger = logging.getLogger(__name__)



router = APIRouter(
    prefix="/api/jobs",
    tags=["jobs"], 
)




@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(payload: JobCreate, db: AsyncSession = Depends(get_db), current_user = Depends(get_authenticated_user), redis: Redis = Depends(get_redis)) -> Job:
    return await create_job_service(payload, db, current_user.id, redis)

@router.get("/", response_model=list[JobResponse])
async def get_jobs(
    db: AsyncSession = Depends(get_db), 
    current_user = Depends(get_authenticated_user), 
    redis: Redis = Depends(get_redis), 
    statistics_redis: Redis = Depends(get_statistics_redis), 
    search: str | None = None
    ) -> list[Job]:

    jobs = await get_jobs_service(db, current_user.id, redis, search)

    if search is None:
        try:
            # Пытаемся получить блокировку
            lock_acquired = await acquire_statistics_lock(
                statistics_redis,
                current_user.id,
            )

            # Если блокировка получена, отправляем задачу Celery
            if lock_acquired:
                calculate_job_statistics.delay(current_user.id)

        except Exception:
            logger.exception(
                "Failed to schedule job statistics for user %s",
                current_user.id,
            )

    return jobs



@router.get("/statistics")
async def get_jobs_statistics(
    current_user=Depends(get_authenticated_user),
    statistics_redis: Redis = Depends(get_statistics_redis),
):
    statistics = await get_job_statistics(
        statistics_redis,
        current_user.id,
    )

    if statistics is None:
        return {
            "status": "processing",
            "statistics": None,
        }

    return {
        "status": "ready",
        "statistics": statistics,
    }

    






@router.post("/register")
async def register_user(payload: UserCreateLogin, db: AsyncSession = Depends(get_db)) -> UserResponse:
    return await create_user(payload, db)  


@router.post("/login")
async def login_user(payload: UserCreateLogin, db: AsyncSession = Depends(get_db), redis: Redis = Depends(get_redis)) -> UserLoginResponse:
    return await login_new_user(payload, db, redis)


@router.patch("/update")
async def change_password(payload: UserCreateLogin, db: AsyncSession = Depends(get_db)) -> UserLoginResponse:
    return await change_password_services(payload, db)


@router.delete("/me")
async def delete_user(db: AsyncSession = Depends(get_db), current_user = Depends(get_authenticated_user)) -> dict:
    await delete_user_services(current_user, db)
    return {"message": "User deleted successfully"}

@router.get("/history")
async def get_user_history(db: AsyncSession = Depends(get_db), current_user = Depends(get_authenticated_user), redis: Redis = Depends(get_redis)) -> list[dict]:
    return await get_user_history_services(redis, current_user.id)




@router.get("/redis-health")
async def redis_health(
    redis: Redis = Depends(get_redis)
):
    await redis.set("job_tracker:health_check", "Redis is working", ex=30)

    value = await redis.get("job_tracker:health_check")

    return {
        "redis": "connected",
        "test_value": value,
    }









@router.get("/{job_id}", response_model=JobResponse) 
async def get_job(job_id: int, db: AsyncSession = Depends(get_db), current_user = Depends(get_authenticated_user), redis: Redis = Depends(get_redis)) -> Job:
    return await get_job_service(job_id, db, redis, current_user.id)


@router.patch("/{job_id}", response_model=JobResponse)
async def update_job(job_id: int, payload: JobUpdate, db: AsyncSession = Depends(get_db), current_user = Depends(get_authenticated_user), redis: Redis = Depends(get_redis)) -> Job:
    return await update_job_service(job_id, payload, db, current_user.id, redis)

@router.delete("/{job_id}", response_model=JobResponse)
async def delete_job(job_id: int, db: AsyncSession = Depends(get_db), current_user = Depends(get_authenticated_user), redis: Redis = Depends(get_redis)) -> Job:
    return await delete_job_service(job_id, db, current_user.id, redis)





