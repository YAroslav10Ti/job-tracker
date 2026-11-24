from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import JobCreate, JobUpdate, UserCreateLogin, UserResponse, UserLoginResponse
from app.models import Job
from app.repository.jobs import (
    get_job_repository,
    create_job_repository,
    get_jobs_repository,
    delete_job_repository,
    get_job_by_name_repository,
    get_current_user,
    create_new_user,
    delete_user_repository
)

from app.security import verify_password, create_access_token
from app.redis.history import add_user_history, get_user_history
from app.redis.rate_limit import check_rate_limit
from app.schemas import JobResponse 
from app.models import User
from redis.asyncio import Redis
import json
import logging

from app.kafka.producer import send_event
from app.kafka.schemas import JobEvent


logger = logging.getLogger(__name__)



async def save_history_safely(
    redis: Redis,
    user_id: int,
    action: str,
    details: dict
):
    try:
        await add_user_history(
            redis=redis,
            user_id=user_id,
            action=action,
            details=details
        )
    except Exception:
        logger.exception(
            "Failed to save user history: user_id=%s, action=%s",
            user_id,
            action
        )



async def create_job_service(payload: JobCreate, db: AsyncSession, id: int, redis: Redis) -> JobResponse:#---------------------------------------------------------
    # создать новую запись о вакансии
    new_job = Job(
        company=payload.company,
        position=payload.position,
        url=payload.url,
        status=payload.status,
        last_date=payload.last_date,
        notes=payload.notes,
        user_id=id
    )

    try:
        # сохранить ее в базу данных
        create_job_repository(new_job, db)
        await db.commit()
        await db.refresh(new_job)
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create job")

    async for key in redis.scan_iter(f"jobs:user:{id}:*"):
        await redis.delete(key)

    try:
        event = JobEvent(
            event_type="job.created",
            user_id=id,
            data={
                "job_id": new_job.id,
                "company": new_job.company,
                "position": new_job.position,
                "status": new_job.status,
            },
        )

        await send_event("jobs", event)

    except Exception:
        logger.exception(
            "Failed to publish job.created event: job_id=%s",
            new_job.id,
        )

    return JobResponse.model_validate(new_job)


async def get_jobs_service(#---------------------------------------------------------
        db: AsyncSession, 
        id: int, 
        redis: Redis, 
        search: str | None = None
    ) -> list[JobResponse]:

    cache_key = f"jobs:user:{id}:{search or 'all'}"
    cached_jobs = await redis.get(cache_key)

    if cached_jobs is not None:
        jobs_data = json.loads(cached_jobs)
        return [
            JobResponse.model_validate(job)
            for job in jobs_data
        ]

    if search:
        jobs = await get_job_by_name_repository(db, id, search)
    else:
        jobs = await get_jobs_repository(db, id)

    jobs_data = [
        JobResponse.model_validate(job).model_dump(mode="json")
        for job in jobs
    ]

    await redis.set(
        cache_key,
        json.dumps(jobs_data),
        ex=300
    )

    return [JobResponse.model_validate(job) for job in jobs]


async def get_job_service(job_id: int, db: AsyncSession, redis: Redis, id: int) -> JobResponse:#---------------------------------------------------------
    cache_key = f"job:user:{id}:{job_id}"

    cached_job = await redis.get(cache_key) 

    if cached_job is not None:
        jobs_data = json.loads(cached_job)

        return JobResponse.model_validate(jobs_data)

    job = await get_job_repository(job_id, db, id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    await redis.set(
        cache_key,
        json.dumps(JobResponse.model_validate(job).model_dump(mode="json")),
        ex=300
    )

    return JobResponse.model_validate(job)





async def update_job_service(
    job_id: int,
    payload: JobUpdate,
    db: AsyncSession,
    id: int,
    redis: Redis
) -> JobResponse:

    # 1. Получаем вакансию из PostgreSQL
    current_job = await get_job_repository(job_id, db, id)

    if current_job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    # 2. Сохраняем старый статус
    old_status = current_job.status

    # 3. Получаем только поля, переданные пользователем
    new_data = payload.model_dump(exclude_unset=True)

    # 4. Изменяем объект вакансии
    for key, value in new_data.items():
        setattr(current_job, key, value)

    # 5. Сохраняем изменения в PostgreSQL
    try:
        await db.commit()
        await db.refresh(current_job)

    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to update job"
        )

    # 6. Удаляем устаревший кэш Redis
    await redis.delete(f"job:user:{id}:{job_id}")

    async for key in redis.scan_iter(f"jobs:user:{id}:*"):
        await redis.delete(key)

    # 7. Отправляем событие в Kafka
    try:
        if "status" in new_data and old_status != current_job.status:
            event_type = "job.status_changed"
        else:
            event_type = "job.updated"

        event = JobEvent(
            event_type=event_type,
            user_id=id,
            data={
                "job_id": current_job.id,
                "company": current_job.company,
                "position": current_job.position,
                "status": current_job.status,
                "old_status": old_status,
            },
        )

        await send_event("jobs", event)

    except Exception:
        logger.exception(
            "Failed to publish job update event: job_id=%s",
            current_job.id,
        )

    # 9. Возвращаем обновлённую вакансию
    return JobResponse.model_validate(current_job)


    


async def delete_job_service(
    job_id: int,
    db: AsyncSession,
    id: int,
    redis: Redis
) -> JobResponse:

    # Получаем вакансию
    current_job = await get_job_repository(job_id, db, id)

    if current_job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    # Сохраняем данные до удаления
    deleted_job_data = {
        "job_id": current_job.id,
        "company": current_job.company,
        "position": current_job.position,
        "status": current_job.status,
    }

    # Создаём ответ API до удаления
    deleted_job = JobResponse.model_validate(current_job)

    # Удаляем вакансию из PostgreSQL
    try:
        await delete_job_repository(current_job, db)
        await db.commit()

    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to delete job"
        )

    # Удаляем кэш Redis
    await redis.delete(f"job:user:{id}:{job_id}")

    async for key in redis.scan_iter(f"jobs:user:{id}:*"):
        await redis.delete(key)

    # Отправляем событие в Kafka
    try:
        event = JobEvent(
            event_type="job.deleted",
            user_id=id,
            data=deleted_job_data,
        )

        await send_event("jobs", event)

    except Exception:
        logger.exception(
            "Failed to publish job delete event: job_id=%s",
            job_id,
        )

    return deleted_job




async def create_user(payload: UserCreateLogin, db: AsyncSession) -> UserResponse:
    current_user = await get_current_user(payload.email, db)

    if current_user is not None:
        raise HTTPException(status_code=400, detail="User is already exist")
    
    try:
        new_user = await create_new_user(payload, db)
        await db.commit()
        await db.refresh(new_user)
        return new_user
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create user") 




async def login_new_user(payload: UserCreateLogin, db: AsyncSession, redis: Redis) -> UserLoginResponse:
    key = f"login_attempts:{payload.email.lower()}"

    allowed = await check_rate_limit(redis, key, limit=5, window=60)

    if not allowed:
        raise HTTPException (status_code=429, detail="Too many login attempts. Please try again later.")

    current_user = await get_current_user(payload.email, db)

    if current_user is None:
        raise HTTPException(status_code=400, detail="User is not exist")

    if not verify_password(payload.password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Password is wrong")

    access_token = create_access_token(current_user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# async def change_password_services(payload: UserCreateLogin, db: AsyncSession) -> UserLoginResponse:
#     current_user = await get_current_user(payload.email, db)

#     if current_user is None:
#         raise HTTPException(status_code=400, detail="User is not exist")

#     hashed_password = hash_password(payload.password)

#     await reset_new_password(current_user, hashed_password, db)

#     try:
#         await db.commit()
#         await db.refresh(current_user)
#     except Exception:
#         await db.rollback()
#         raise HTTPException(status_code=500, detail="Failed to change password")

#     access_token = create_access_token(current_user.id)

#     return {
#         "access_token": access_token,
#         "token_type": "bearer"
#     }


async def delete_user_services(user: User, db: AsyncSession) -> dict:
    try:
        await delete_user_repository(user, db)
        await db.commit()
        return {"message": "User deleted successfully"}
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete user")


async def get_user_history_services(redis: Redis, user_id: int) -> list[dict]:
    try:
        history = await get_user_history(redis, user_id)
        return history
    except Exception:
        logger.exception(
            "Failed to retrieve user history: user_id=%s",
            user_id
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve user history")
    




async def get_user_insights(
    user_id: int,
    redis: Redis,
) -> dict:
    key = f"user:{user_id}:job_insights"

    # Получаем все счётчики из Redis
    stats = await redis.hgetall(key)

    # Преобразуем значения из Redis в числа
    total = int(stats.get("total", 0))
    interview = int(stats.get("interview", 0))
    rejected = int(stats.get("rejected", 0))

    # Рассчитываем проценты
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
    
    


        







