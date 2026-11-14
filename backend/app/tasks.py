import os

from celery import Task
from redis import Redis
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

from app.celery_app import celery_app
from app.models import Job
from app.redis.statistics import save_job_statistics


DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise RuntimeError("DATABASE_URL is not set")

SYNC_DATABASE_URL = DATABASE_URL.replace(
    "postgresql+asyncpg://",
    "postgresql+psycopg://",
)


engine = create_engine(
    SYNC_DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocalSync = sessionmaker(bind=engine)


JOB_STATUSES = (
    "Заинтересован",
    "Подана заявка",
    "Собеседование",
    "Отклонена",
)


@celery_app.task
def calculate_job_statistics(user_id: int):

    with SessionLocalSync() as db:

        result = db.execute(
            select(
                Job.status,
                func.count(Job.id),
            )
            .where(Job.user_id == user_id)
            .group_by(Job.status)
        )

        statistics = {
            status: 0
            for status in JOB_STATUSES
        }

        for status, count in result.all():
            if status in statistics:
                statistics[status] = count

    redis_url = os.getenv(
        "REDIS_STATISTICS_URL",
        "redis://redis:6379/2",
    )

    with Redis.from_url(
        redis_url,
        decode_responses=True,
    ) as redis:

        save_job_statistics(
            redis=redis,
            user_id=user_id,
            statistics=statistics,
        )

    return statistics