from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis

from app.core.config import REDIS_URL
from app.routers.jobs import router as jobs_router

from contextlib import asynccontextmanager

from app.kafka.producer import (
    start_kafka_producer,
    stop_kafka_producer,
)
from app.routers import insights


@asynccontextmanager
async def lifespan(app: FastAPI):

    # Создаём Redis-клиент DB 0
    redis = Redis.from_url(
        REDIS_URL,
        decode_responses=True,
    )

    # Создаём Redis-клиент DB 2
    statistics_redis = Redis.from_url(
        os.getenv(
            "REDIS_STATISTICS_URL",
            "redis://redis:6379/2",
        ),
        decode_responses=True,
    )

    await start_kafka_producer()

    try:
        # Проверяем DB 0
        await redis.ping()
        app.state.redis = redis

        print("Redis DB 0 connected successfully")

        # Проверяем DB 2
        await statistics_redis.ping()
        app.state.statistics_redis = statistics_redis

        print("Redis DB 2 connected successfully")

        yield

    finally:
        # Закрываем оба подключения
        await redis.aclose()
        await statistics_redis.aclose()
        await stop_kafka_producer()

        print("Redis connections closed")


app = FastAPI(
    title="Job Tracker API",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:5501",
        "http://127.0.0.1:5501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(jobs_router)
app.include_router(insights.router)


@app.get("/")
def root():
    return {"message": "Job Tracker API is running"}